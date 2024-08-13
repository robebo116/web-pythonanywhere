from flask import Flask, request, jsonify, redirect, url_for, render_template, session, send_from_directory
import re
from datetime import timedelta, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(minutes=180)

def load_credentials(filename):
    credentials = {}
    with open(filename, 'r') as file:
        for line in file:
            username, password = line.strip().split(':')
            credentials[username] = password
    return credentials

CREDENTIALS = load_credentials('credentials.txt')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in CREDENTIALS and CREDENTIALS[username] == password:
            session.permanent = True
            session['user_id'] = username
            session['login_time'] = datetime.now().timestamp()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            error = 'Invalid credentials'
            return render_template('index.html', error=error)
    return render_template('index.html', error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    if 'login_time' in session:
        elapsed_time = datetime.now().timestamp() - session['login_time']
        if elapsed_time > app.permanent_session_lifetime.total_seconds():
            return redirect(url_for('logout'))
    return render_template('home.html')

@app.route('/send-link', methods=['POST'])
@login_required
def send_link():
    if 'login_time' in session:
        elapsed_time = datetime.now().timestamp() - session['login_time']
        if elapsed_time > app.permanent_session_lifetime.total_seconds():
            return jsonify({"status": "error", "message": "Session expired"}), 401
    link = request.form.get('link')

    match = re.search(r'chess\.com.*?/(\d+)', link)
    if match:
        number = match.group(1)
        link = f'https://www.chess.com/analysis/game/live/{number}?tab=review'
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Link format is incorrect"}), 400

@app.before_request
def check_session_expiration():
    if 'user_id' in session and 'login_time' in session:
        elapsed_time = datetime.now().timestamp() - session['login_time']
        if elapsed_time > app.permanent_session_lifetime.total_seconds():
            session.clear()
            return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)