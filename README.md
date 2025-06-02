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
- **Database**: PostgreSQL
- **API Gateway**: Kong
- **Containerization**: Docker, Docker Compose

## Requirements

- Docker and Docker Compose

## Setup and Installation

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

   Or through the API Gateway:
   ```
   http://localhost:8080/api/web/
   ```

   Note: The API Gateway (Kong) is configured to serve the web UI directly at:
   ```
   http://localhost:8080/
   ```

## Environment Variables

The application uses environment variables for configuration. These are stored in a `.env` file at the root of the project. A sample `.env` file is provided below:

```
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True

# Database settings
POSTGRES_DB=iptv_manager
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# CORS settings
CORS_ALLOW_ALL_ORIGINS=True
```

To use a different configuration:
1. Create a `.env` file in the project root
2. Set the appropriate values for your environment
3. The application will automatically load these values

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

```
docker-compose exec web python manage.py migrate
```

### Creating a Superuser

```
docker-compose exec web python manage.py createsuperuser
```

## API Endpoints

All API endpoints are accessible directly or through the Kong API Gateway:

- Direct access:
  - `/api/server-time/` - Get current server time
  - `/api/resource-utilization/` - Get CPU and memory usage

- Via API Gateway:
  - `/api/web/api/server-time/` - Get current server time
  - `/api/web/api/resource-utilization/` - Get CPU and memory usage
  - `/api/playlist-manager/...` - Access Playlist Manager endpoints

## API Gateway

The project uses Kong as an API Gateway to route requests to the appropriate backend services:

- Web service (Django): `/api/web/*`
- Playlist Manager service (.NET): `/api/playlist-manager/*`
- Web UI (Django): `/` (serves the web UI directly)

For more details on the API Gateway configuration, see the [Kong README](config/kong/README.md).

## WebSocket Endpoints

- `/ws/system-stats/` - Real-time system statistics updates

## License

This project is licensed under the MIT License - see the LICENSE file for details.
