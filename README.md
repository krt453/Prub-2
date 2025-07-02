# Game Panel

This repository contains a Flask-based panel to manage Dockerized game servers.

## Structure

- `game-panel/backend/` – Flask app with authentication and server management.
- `game-panel/frontend/` – Placeholder for future frontend code.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r game-panel/backend/requirements.txt
   ```
2. Set environment variables for secret key and database connection, e.g.:
   ```bash
   export SECRET_KEY=changeme
   export DATABASE_URI=mysql+pymysql://user:password@localhost/gamepanel
   ```
3. Run the application:
   ```bash
   python game-panel/backend/app.py
   ```
   The app will create the required tables on first run.

## Features

- Login system with hashed passwords and simple roles.
- Create, start, stop, restart and delete game servers using Docker Compose.
- Basic pages to list servers, view details/logs and create new ones.
