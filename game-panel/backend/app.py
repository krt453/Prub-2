from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URI',
    'mysql+pymysql://user:password@localhost/gamepanel',
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

BASE_COMPOSE_DIR = os.path.join(os.getcwd(), 'compose', 'game-servers')


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')


class GameServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    compose_path = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='stopped')
    container_id = db.Column(db.String(64))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    servers = GameServer.query.all()
    return render_template('index.html', servers=servers)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


def _compose_cmd(server, action):
    cmd = ['docker', 'compose', '-f', server.compose_path]
    if action == 'start':
        cmd += ['up', '-d']
    elif action == 'stop':
        cmd += ['stop']
    elif action == 'restart':
        cmd += ['restart']
    elif action == 'down':
        cmd += ['down']
    subprocess.run(cmd, cwd=os.path.dirname(server.compose_path))


@app.route('/servers/<int:server_id>/start')
@login_required
def start_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    _compose_cmd(server, 'start')
    server.status = 'running'
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/<int:server_id>/stop')
@login_required
def stop_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    _compose_cmd(server, 'stop')
    server.status = 'stopped'
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/<int:server_id>/restart')
@login_required
def restart_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    _compose_cmd(server, 'restart')
    server.status = 'running'
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/<int:server_id>/delete')
@login_required
def delete_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    _compose_cmd(server, 'down')
    db.session.delete(server)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/new', methods=['GET', 'POST'])
@login_required
def new_server():
    if request.method == 'POST':
        name = request.form['name']
        game_type = request.form['game_type']
        server_dir = os.path.join(BASE_COMPOSE_DIR, name)
        os.makedirs(server_dir, exist_ok=True)
        compose_path = os.path.join(server_dir, 'docker-compose.yml')
        with open(compose_path, 'w') as f:
            f.write(f"version: '3'\nservices:\n  {name}:\n    image: {game_type}\n    container_name: {name}\n")
        server = GameServer(
            name=name,
            game_type=game_type,
            compose_path=compose_path,
            status='stopped',
        )
        db.session.add(server)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_server.html')


@app.route('/servers/<int:server_id>')
@login_required
def server_detail(server_id):
    server = GameServer.query.get_or_404(server_id)
    logs = ''
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', server.compose_path, 'logs', '--tail', '20'],
            cwd=os.path.dirname(server.compose_path),
            capture_output=True,
            text=True,
        )
        logs = result.stdout
    except Exception:
        logs = 'Unable to get logs.'
    return render_template('detail.html', server=server, logs=logs)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
