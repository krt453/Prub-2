# Game Panel


- `game-panel/frontend/` – Placeholder for future frontend code.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r game-panel/backend/requirements.txt
   ```

2. Set environment variables and create the database:
   ```bash
   export SECRET_KEY=your-secret-key
   export DATABASE_URI=mysql+pymysql://user:password@localhost/gamepanel
   export COMMAND_TOKEN=choose-a-command-token
   ```

3. Run the application:
   ```bash
   python game-panel/backend/app.py
   ```


