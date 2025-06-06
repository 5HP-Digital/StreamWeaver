# IPTV Manager

A web application for managing IPTV services, TV schedules, and more.

## Features

- Real-time server monitoring (CPU and memory usage)
- IPTV management (coming soon)
- TV Schedule (coming soon)
- Settings management (coming soon)

## Technology Stack

- **Backend**: Django, Django REST Framework, Channels (WebSockets)
- **Frontend**: Vue.js, Bootstrap 5, Chart.js
- **Database**: SQLite3
- **Containerization**: Docker, Docker Compose

## Requirements

### For Docker Setup
- Docker and Docker Compose

### For Local Setup
- Python 3.12 or later
- pip (Python package manager)
- Git

## Setup and Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/iptv-manager.git
   cd iptv-manager
   ```

2. Start the application using Docker Compose:
   ```
   docker-compose up -d
   ```

3. Access the application in your browser:
   ```
   http://localhost:8000
   ```

### Without Docker

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/iptv-manager.git
   cd iptv-manager
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   cd iptv_manager
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the `iptv_manager` directory with the following content:
   ```
   # Django settings
   SECRET_KEY="your-secret-key"
   DEBUG=True

   # Database settings
   # SQLite3 is used by default, no additional configuration needed

   # CORS settings
   CORS_ALLOW_ALL_ORIGINS=True
   ```

5. Apply database migrations:
   ```
   python manage.py migrate
   ```

6. Start the development server:
   ```
   # Using Django's development server
   python manage.py runserver

   # Or using Daphne (ASGI server, recommended for WebSocket support)
   daphne -b 0.0.0.0 -p 8000 iptv_manager.asgi:application
   ```

7. Access the application in your browser:
   ```
   http://localhost:8000
   ```

## Environment Variables

The application uses environment variables for configuration. These are stored in a `.env` file in the `iptv_manager` directory. A sample `.env` file is provided in the setup instructions above.

Key environment variables include:
- `SECRET_KEY`: Django's secret key for security
- `DEBUG`: Set to True for development, False for production
- `CORS_ALLOW_ALL_ORIGINS`: Controls CORS settings

Note: The `.env` file is included in `.gitignore` to prevent sensitive information from being committed to the repository.

## Development

### Project Structure

```
iptv_manager/
├── iptv_manager/          # Django project settings
├── home/                  # Home app (dashboard, system stats)
│   ├── api/               # REST API endpoints
│   └── ...
├── templates/             # HTML templates
│   ├── base.html          # Base template with navigation
│   └── home/              # Home app templates
├── static/                # Static files (CSS, JS, images)
└── ...
```

### Running Migrations

#### With Docker
```
docker-compose exec web python manage.py migrate
```

#### Without Docker
```
# Make sure you're in the iptv_manager directory with your virtual environment activated
python manage.py migrate
```

### Collecting Static Files

Django needs to collect all static files from various applications into a single location for production deployment. This is handled by the `collectstatic` command.

```
# Make sure you're in the iptv_manager directory with your virtual environment activated
python manage.py collectstatic --noinput
```

Note: The `--noinput` flag prevents Django from asking for confirmation. The collected static files are stored in the `staticfiles` directory, which is excluded from version control.

### Creating a Superuser

#### With Docker
```
docker-compose exec web python manage.py createsuperuser
```

#### Without Docker
```
# Make sure you're in the iptv_manager directory with your virtual environment activated
python manage.py createsuperuser
```

## API Endpoints

The following API endpoints are available:

- `/api/server-time/` - Get current server time
- `/api/resource-utilization/` - Get CPU and memory usage
- `/api/sources/` - Access playlist sources
- `/api/sources/<id>/channels/` - Access channels for a specific source

## WebSocket Endpoints

- `/ws/system-stats/` - Real-time system statistics updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.
