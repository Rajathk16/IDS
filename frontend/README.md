# DEVRAKSHAK Next.js Frontend

This is the Next.js 14 frontend for the DEVRAKSHAK AI IoT Intrusion & DDoS Defense System.

## Architecture
- **Frontend**: Next.js 14, React 18, Tailwind CSS, Lucide Icons (Port 3000)
- **Backend**: Python 3.14 IDSEngine, scikit-learn, joblib, SQLite (Port 8000)
- **Dataset**: Official CICIoT2023 dataset partitions (`data/raw/MERGED_CSV/Merged01.csv` ... `Merged63.csv`)

## Running

### Option 1: 1-Click Launch (Windows)
Double-click `start_fullstack.bat` in the root project folder.

### Option 2: Manual Terminal Commands
1. Start the Python Backend (in root folder):
   ```powershell
   uv run python src/web_server.py --port 8000
   ```
2. Start the Next.js Frontend (in `frontend/` folder):
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
3. Open `http://localhost:3000` in your web browser.

