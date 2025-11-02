# Balance Sheet Analysis ChatGPT Application

A full-stack web application for analyzing company balance sheets using AI-powered chat functionality. Built with Django (backend) and React (frontend).

## Features

- **Role-Based Access Control**: Three user roles - Analyst, CEO, and Group Owner
- **AI-Powered Analysis**: Chat with Gemini Pro AI to analyze company performance
- **PDF Processing**: Upload and extract data from balance sheet PDFs
- **Financial Visualization**: Interactive charts showing trends and comparisons
- **Hierarchical Company Structure**: Support for parent companies and subsidiaries
- **Secure Authentication**: JWT-based authentication system

## Technology Stack

### Backend
- Django 5.2.7
- Django REST Framework
- JWT Authentication (djangorestframework-simplejwt)
- SQLite (designed for easy MySQL migration)
- Gemini Pro API for AI analysis
- pdfplumber for PDF processing

### Frontend
- React 18
- React Router
- Tailwind CSS
- Recharts for visualization
- Axios for API calls

## Installation

### Backend Setup

1. Navigate to the project directory:
```bash
cd /Users/rishi/Personal/Elimentary
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file in backend directory
echo "GEMINI_API_KEY=your_api_key_here" > backend/.env
echo "DEBUG=True" >> backend/.env
```

5. Run migrations:
```bash
python backend/manage.py migrate
```

6. Create superuser:
```bash
python backend/manage.py createsuperuser
```

7. Run development server:
```bash
python backend/manage.py runserver
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Configuration

### Gemini API Setup

1. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to `backend/.env`:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### User Roles

- **Analyst**: Can upload balance sheets, access all companies for analysis
- **CEO**: Can only view their assigned company's data and chat
- **Group Owner**: Can view all subsidiary companies under their group

## Usage

1. Register/Login to the application
2. Select a company from the sidebar
3. Use Chat Analysis to ask questions about company performance
4. View Analytics for visual representations of financial data
5. Analysts can upload balance sheet PDFs

## Sample Data

To process the Reliance balance sheet:

1. Download the PDF from the provided link
2. Use the admin panel or API to create companies (Reliance Industries, Jio Platforms, Reliance Retail Ventures)
3. Create user accounts with appropriate roles
4. Upload the balance sheet PDFs

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login (returns JWT tokens)
- `POST /api/auth/token/refresh/` - Refresh access token
- `GET /api/auth/profile/` - Get user profile

### Companies
- `GET /api/companies/` - List accessible companies
- `GET /api/companies/{id}/` - Company details
- `GET /api/companies/{id}/subsidiaries/` - Get subsidiaries

### Balance Sheets
- `POST /api/balance-sheets/` - Upload balance sheet (Analysts only)
- `GET /api/balance-sheets/?company={id}` - List balance sheets
- `GET /api/balance-sheets/{id}/analytics/` - Get analytics data

### Chat
- `POST /api/chat/query/` - Send query, get AI response
- `GET /api/chat/history/?company={id}` - Get chat history

## Admin Panel

Access the Django admin panel at `http://localhost:8000/admin` to:
- Manage users, companies, and balance sheets
- Set up company hierarchies
- Assign user-company access
- View uploaded PDFs and extracted data

## Database Migration to MySQL

The database schema is designed for easy migration to MySQL:

1. Update `backend/config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_database_name',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

2. Install MySQL client:
```bash
pip install mysqlclient
```

3. Run migrations:
```bash
python backend/manage.py migrate
```

## Development

### Running Tests
```bash
python backend/manage.py test
```

### Linting
```bash
# Backend
flake8 backend/
black backend/

# Frontend
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Google Gemini Pro for AI capabilities
- Django community for excellent framework
- React team for powerful UI library

