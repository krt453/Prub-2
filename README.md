# Game Panel

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
