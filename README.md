# Map Application

A web application that allows users to upload and visualize geographical data, create custom shapes, and manage markers on a map.

## Features

- User Authentication (Register/Login)
- File Upload Support (GeoJSON/KML)
- Interactive Map Visualization using Mapbox
- Custom Shape Drawing & Editing
- Point Marker Management
- Dataset Visibility Control

## Tech Stack

### Backend
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- JWT Authentication
- SQLite

### Frontend
- Vue 3 (JavaScript framework)
- Quasar Framework (UI components)
- Pinia (State management)
- Mapbox GL JS (Map visualization)
- Axios (HTTP client)

## Prerequisites

- Python 3.10+
- Node.js 16+
- npm or yarn
- Quasar CLI (`npm install -g @quasar/cli`)

## Setup & Installation

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/Parth1998D/SkyServe-FullStack.git
cd SkyServe-FullStack
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file in backend directory:
```env
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./app.db  # For development
```

5. Run the backend server:
```bash
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
# Using yarn
yarn

# Using npm
npm install
```

3. Create `.env.local` file:
```env
API_URL=http://localhost:8000
MAPBOX_ACCESS_TOKEN=your-mapbox-token-here
```

4. Run development server:
```bash
# Using Quasar CLI
quasar dev

# Using yarn
yarn dev

# Using npm
npm run dev
```

The frontend application will be available at `http://localhost:9000`

## API Documentation

Once the backend server is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Deployment

### Backend Deployment (Render.com)

(In free plan, initial load will take a minute to restart after inactivity)
Live Backend URL: https://skyserve-backend-b2o1.onrender.com

API documentation is available at:
- Swagger UI: `https://skyserve-backend-b2o1.onrender.com/docs`
- ReDoc: `https://skyserve-backend-b2o1.onrender.com/redoc`

### Frontend Deployment (Netlify)

1. Create production environment file `.env.prod` 
2. Build the application:
```bash
# Using Quasar CLI
quasar build

# Using yarn
yarn build

# Using npm
npm run build
```

3. Deploy the `dist/spa` folder to your preferred hosting service

Live Frontend URL: https://skyserve-assignment.netlify.app/

## Development Guidelines

### API Endpoints:
- User authentication: `/token` (login) and `/users` (register)
- File upload: `/datasets`
- Shape management: `/shapes`

### Frontend Routes:
- `/login` - User login/register
- `/` - Main map interface

## Quasar CLI Commands

```bash
# Install Quasar CLI globally
npm install -g @quasar/cli

# Start development server
quasar dev

# Build for production
quasar build
```

## Additional Notes

- Make sure to replace the Mapbox access token with your own
- For production, update CORS settings in the backend to match your frontend domain
- Keep your SECRET_KEY secure and different in production
- PostgreSQL is recommended for production use
