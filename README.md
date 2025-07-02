# Game Panel

This repository contains a Flask-based panel to manage Dockerized game servers.

## Structure

- `game-panel/backend/` – Flask app for managing game servers.
- `game-panel/frontend/` – Placeholder for future frontend code.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r game-panel/backend/requirements.txt
   ```
2. Set the database connection string:
   ```bash
   export DATABASE_URI=mysql+pymysql://user:password@localhost/gamepanel
   ```
3. Run the application:
   ```bash
   python game-panel/backend/app.py
   ```
   The app will create the required tables on first run.

## Features

- Create, start, stop, restart and delete game servers using Docker Compose.
- Basic pages to list servers, view details/logs and create new ones.
