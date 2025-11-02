# Quick Start Guide

## Prerequisites

- Python 3.9+
- Node.js 16+
- npm

## Setup (5 minutes)

### 1. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure Gemini API Key (Optional for now)
# Edit backend/.env and add: GEMINI_API_KEY=your_key_here

# Create database and superuser
python backend/manage.py migrate
python backend/manage.py createsuperuser

# Create sample data
python backend/manage.py create_sample_data

# Start server
python backend/manage.py runserver
```

Backend runs on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173`

## Testing the Application

### Login with Sample Users

1. Open `http://localhost:5173`
2. Register a new user OR login with:
   - Analyst: `analyst` / `analyst123` (can see all companies, upload PDFs)
   - Jio CEO: `jio_ceo` / `ceo123` (can only see Jio Platforms)
   - Retail CEO: `retail_ceo` / `ceo123` (can only see Reliance Retail)
   - Group Owner: `group_owner` / `owner123` (can see all companies)

### Key Features to Test

1. **Company Selection**: Select different companies from sidebar
2. **Chat Analysis**: Ask questions like:
   - "What is the revenue trend?"
   - "Compare assets vs liabilities"
   - "Show me the growth rate"
3. **Analytics**: View charts for revenue, assets, liabilities
4. **Upload**: (Analyst only) Upload a PDF balance sheet

### Upload a Balance Sheet

1. Login as Analyst
2. Select a company
3. Go to "Upload Balance Sheet" tab
4. Choose a PDF file
5. Enter year (and optional quarter)
6. Click "Upload Balance Sheet"

Note: Make sure GEMINI_API_KEY is set in backend/.env for chat to work properly.

## Admin Panel

Access at `http://localhost:8000/admin` to:
- Manage users and companies
- View uploaded balance sheets
- Assign company access
- Set up hierarchies

Login with superuser credentials created above.

## Troubleshooting

### "Module not found" errors
- Make sure virtual environment is activated
- Run `pip install -r backend/requirements.txt` again

### Frontend not connecting to backend
- Ensure backend is running on port 8000
- Check `frontend/src/utils/axiosConfig.js` for correct base URL

### Chat not working
- Add your Gemini API key to `backend/.env`
- Get free key at: https://makersuite.google.com/app/apikey

### Database errors
- Run `python backend/manage.py migrate`
- Delete `db.sqlite3` and re-run migrations

## Next Steps

1. Get your Gemini API key for chat functionality
2. Upload real balance sheet PDFs
3. Customize company hierarchy
4. Add more users with different roles
5. Test role-based access control

## Support

For issues or questions, refer to the main README.md

