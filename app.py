import os
import requests
from flask import Flask, render_template_string, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'al_huda_production_fallback_key_9876')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'quran_users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Al Quran Web Portal</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #ffffff; color: #000000; margin: 0; padding: 0; line-height: 1.6; }
        nav { background: #000000; color: #ffffff; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        nav a { color: #ffffff; text-decoration: none; margin-left: 15px; font-weight: bold; }
        .container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
        .card { border: 1px solid #000000; padding: 20px; margin-bottom: 15px; background: #ffffff; border-radius: 4px; }
        .btn { background: #000000; color: #ffffff; padding: 10px 20px; border: none; text-decoration: none; display: inline-block; cursor: pointer; font-weight: bold; border-radius: 4px; }
        .btn:hover { background: #333333; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #000000; border-radius: 4px; box-sizing: border-box; }
        .flash { padding: 10px; border: 1px solid #000000; margin-bottom: 20px; background-color: #f0f0f0; color: #000000; }
        @font-face { font-family: 'Amiri'; src: url('https://googleapis.com'); }
    </style>
</head>
<body>
    <nav>
        <a href="{{ url_for('index') }}" style="font-size: 1.3rem; margin: 0;">📖 Al Quran Portal</a>
        <div>
            {% if current_user.is_authenticated %}
                <span style="margin-right: 15px;">Welcome, <strong>{{ current_user.username }}</strong></span>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('register') }}">Register</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

INDEX_TEMPLATE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<h2>Quranic Surahs Index</h2>
<p>Select a Surah to read the text and stream recitation by Qari Mishary Rashid Alafasy.</p>
<hr style="border-top: 1px solid #000000; margin-bottom: 20px;">
<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px;">
    {% for surah in surahs %}
    <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <strong>{{ surah.id }}. {{ surah.name_simple }}</strong>
            <br><small style="color: #555;">{{ surah.translated_name.name }} • {{ surah.verses_count }} Verses</small>
        </div>
        <a href="{{ url_for('surah', surah_id=surah.id) }}" class="btn" style="padding: 5px 12px; font-size: 0.9rem;">Read</a>
    </div>
    {% endfor %}
</div>
""")

SURAH_TEMPLATE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div style="text-align: center; margin-bottom: 40px;">
    <h2>Surah {{ meta.name_simple }} ({{ meta.name_arabic }})</h2>
    <p><em>{{ meta.translated_name.name }} — Revelation: {{ meta.revelation_place|capitalize }}</em></p>
    
    <div style="margin-top: 20px; background: #ffffff; padding: 15px; border: 1px solid #000000; border-radius: 4px;">
        <label style="display:block; font-weight: bold; margin-bottom: 8px;">🔊 Recitation by Qari Mishary Rashid Alafasy</label>
        <audio controls src="{{ audio_url }}" style="width: 100%; max-width: 500px; color: #000;"></audio>
    </div>
</div>

<a href="{{ url_for('index') }}" class="btn" style="margin-bottom: 20px;">← Back to Index</a>

<div style="margin-top: 20px;">
    {% for verse in surah_data %}
    <div style="border-bottom: 1px solid #000000; padding: 25px 0; display: flex; flex-direction: column; gap: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;">
            <span style="font-weight: bold; border: 1px solid #000; padding: 2px 8px; border-radius: 50%; font-size: 0.85rem;">{{ verse.verse_key }}</span>
            <p dir="rtl" style="font-family: 'Amiri', serif; font-size: 2.2rem; margin: 0; line-height: 2.5; text-align: right; width: 100%; color: #000000;">
                {{ verse.text }}
            </p>
        </div>
        <div style="color: #000000; font-size: 1.1rem; padding-left: 45px;">
            {{ verse.translation|safe }}
        </div>
    </div>
    {% endfor %}
</div>
""")

LOGIN_TEMPLATE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="card" style="max-width: 450px; margin: 50px auto;">
    <h2 style="text-align: center; margin-top: 0;">Sign In</h2>
    <form method="POST">
        <div class="form-group">
            <label for="email">Email Address</label>
            <input type="email" name="email" id="email" required placeholder="name@example.com">
        </div>
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" name="password" id="password" required placeholder="••••••••">
        </div>
        <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">Login</button>
    </form>
    <p style="text-align: center; margin-top: 20px; font-size: 0.9rem;">
        New to the portal? <a href="{{ url_for('register') }}" style="color:#000; font-weight:bold;">Create an account</a>
    </p>
</div>
""")

REGISTER_TEMPLATE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="card" style="max-width: 450px; margin: 50px auto;">
    <h2 style="text-align: center; margin-top: 0;">Create Account</h2>
    <form method="POST">
        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" name="username" id="username" required placeholder="e.g., ahmad_student">
        </div>
        <div class="form-group">
            <label for="email">Email Address</label>
            <input type="email" name="email" id="email" required placeholder="name@example.com">
        </div>
        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" name="password" id="password" required placeholder="••••••••">
        </div>
        <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">Sign Up</button>
    </form>
    <p style="text-align: center; margin-top: 20px; font-size: 0.9rem;">
        Already registered? <a href="{{ url_for('login') }}" style="color:#000; font-weight:bold;">Log in here</a>
    </p>
</div>
""")

@app.route('/')
@login_required
def index():
    response = requests.get("https://quran.com")
    surahs = response.json().get('chapters', []) if response.status_code == 200 else []
    return render_template_string(INDEX_TEMPLATE, surahs=surahs)

@app.route('/surah/<int:surah_id>')
@login_required
def surah(surah_id):
    verses_req = requests.get(f"https://quran.com{surah_id}")
    trans_req = requests.get(f"https://quran.com{surah_id}")
    meta_req = requests.get(f"https://quran.com{surah_id}?language=en")
    
    verses = verses_req.json().get('verses', []) if verses_req.status_code == 200 else []
    translations = trans_req.json().get('translations', []) if trans_req.status_code == 200 else []
    meta = meta_req.json().get('chapter', {}) if meta_req.status_code == 200 else {}
    
    surah_data = []
    for i in range(len(verses)):
        surah_data.append({
            'verse_key': verses[i]['verse_key'],
            'text': verses[i]['text_indopak'],
            'translation': translations[i]['text'] if i < len(translations) else ""
        })
        
    audio_url = f"https://quranicaudio.com{str(surah_id).zfill(3)}.mp3"
    return render_template_string(SURAH_TEMPLATE, surah_data=surah_data, meta=meta, audio_url=audio_url)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
flash('Username or Email already registered.')
return redirect(url_for('register'))
new_user = User(username=username, email=email, password=password)
db.session.add(new_user)
db.session.commit()
flash('Registration successful! Please login.')
return redirect(url_for('login'))
return render_template_string(REGISTER_TEMPLATE)
@app.route('/login', methods=['GET', 'POST'])
def login():
if request.method == 'POST':
email = request.form.get('email')
password = request.form.get('password')
user = User.query.filter_by(email=email).first()
if user and user.password == password:
login_user(user)
return redirect(url_for('index'))
else:
flash('Invalid email or password configuration.')
return render_template_string(LOGIN_TEMPLATE)
@app.route('/logout')
@login_required
def logout():
logout_user()
return redirect(url_for('login'))
if name == 'main':
with app.app_context():
db.create_all()
app.run(debug=True)
