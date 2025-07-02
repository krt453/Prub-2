from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import subprocess
import shlex
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URI',
    'mysql+pymysql://user:password@localhost/gamepanel',
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

BASE_DIR = Path(__file__).resolve().parent
BASE_COMPOSE_DIR = BASE_DIR / 'compose' / 'game-servers'

COMMAND_TOKEN = os.environ.get('COMMAND_TOKEN')


db = SQLAlchemy(app)


class GameServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    compose_path = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='stopped')
    container_id = db.Column(db.String(64))


def _refresh_status(server: GameServer):
    """Update the server.status field based on Docker compose state."""
    result = subprocess.run(
        [
            'docker',
            'compose',
            '-f',
            server.compose_path,
            'ps',
            '-q',
            server.name,
        ],
        cwd=os.path.dirname(server.compose_path),
        capture_output=True,
        text=True,
    )
    container_id = result.stdout.strip()
    server.status = 'running' if container_id else 'stopped'
    server.container_id = container_id or None


@app.route('/')
def index():
    servers = GameServer.query.all()
    for s in servers:
        _refresh_status(s)
    db.session.commit()
    return render_template('index.html', servers=servers)


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
    try:
        subprocess.run(
            cmd,
            cwd=os.path.dirname(server.compose_path),
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        flash(f'Failed to {action} server: {exc}', 'error')
        return False
    return True


@app.route('/servers/<int:server_id>/start')
def start_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    if _compose_cmd(server, 'start'):
        _refresh_status(server)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/<int:server_id>/stop')
def stop_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    if _compose_cmd(server, 'stop'):
        _refresh_status(server)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/<int:server_id>/restart')
def restart_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    if _compose_cmd(server, 'restart'):
        _refresh_status(server)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/<int:server_id>/delete')
def delete_server(server_id):
    server = GameServer.query.get_or_404(server_id)
    if _compose_cmd(server, 'down'):
        db.session.delete(server)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/servers/new', methods=['GET', 'POST'])
def new_server():
    if request.method == 'POST':
        name = request.form['name']
        game_type = request.form['game_type']
        server_dir = BASE_COMPOSE_DIR / name
        os.makedirs(server_dir, exist_ok=True)
        compose_path = server_dir / 'docker-compose.yml'
        with open(compose_path, 'w') as f:
            f.write(
                "version: '3'\n"
                "services:\n"
                f"  {name}:\n"
                f"    image: {game_type}\n"
                f"    container_name: {name}\n"
            )
        server = GameServer(
            name=name,
            game_type=game_type,
            compose_path=str(compose_path),
            status='stopped',
        )
        db.session.add(server)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_server.html')


@app.route('/servers/<int:server_id>')
def server_detail(server_id):
    server = GameServer.query.get_or_404(server_id)
    logs = ''
    try:
        result = subprocess.run(
            [
                'docker',
                'compose',
                '-f',
                server.compose_path,
                'logs',
                '--tail',
                '20',
            ],
            cwd=os.path.dirname(server.compose_path),
            capture_output=True,
            text=True,
            check=True,
        )
        logs = result.stdout
    except subprocess.CalledProcessError as exc:
        logs = f'Unable to get logs: {exc}'
    return render_template('detail.html', server=server, logs=logs)


@app.route('/servers/<int:server_id>/command', methods=['POST'])
def server_command(server_id):
    if COMMAND_TOKEN and request.form.get('token') != COMMAND_TOKEN:
        abort(403)
    server = GameServer.query.get_or_404(server_id)
    command = request.form['command']
    docker_cmd = [
        'docker',
        'compose',
        '-f',
        server.compose_path,
        'exec',
        server.name,
    ] + shlex.split(command)
    try:
        subprocess.run(
            docker_cmd,
            cwd=os.path.dirname(server.compose_path),
            check=True,
        )
        flash('Command sent')
    except subprocess.CalledProcessError as exc:
        flash(f'Command failed: {exc}', 'error')
    return redirect(url_for('server_detail', server_id=server.id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
