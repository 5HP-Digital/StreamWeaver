# Kong API Gateway Configuration

This directory contains the configuration for the Kong API Gateway used in the IPTV Manager project.

## Overview

Kong is used as an API Gateway to route requests to the appropriate backend services:

- Web service (Django): `/api/web/*`
- Playlist Manager service (.NET): `/api/playlist-manager/*`
- Web UI (Django): `/` (serves the web UI directly)

## Configuration

The configuration is defined in the `kong.yml` file using Kong's declarative configuration format. This allows Kong to be run in DB-less mode, which simplifies deployment.

### Services

The following services are defined:

1. **web-service**: Routes requests from `/api/server-time` and `/api/resource-utilization` to the Django web service
   - URL: `http://web:8000`
   - Strip path: `false` (preserves the request path)

2. **playlist-manager-service**: Routes requests from `/api/playlist-manager` to the .NET Playlist Manager service
   - URL: `http://playlist-manager:8080`
   - Strip path: `true` (removes `/api/playlist-manager` from the request path)

3. **web-ui-service**: Serves the web UI directly from the Django web service
   - URL: `http://web:8000`
   - Strip path: `false` (preserves the request path)

### CORS Configuration

Each service has CORS (Cross-Origin Resource Sharing) configured to allow:
- All origins (`*`)
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Origin, Authorization, Content-Type
- Exposed headers: Content-Length

## Usage

The Kong API Gateway is accessible at:
- HTTP: `http://localhost:8080`
- HTTPS: `https://localhost:8443`

Examples:
- Web UI: `http://localhost:8080/`
- Web API: `http://localhost:8080/api/web/api/server-time/`
- Playlist Manager API: `http://localhost:8080/api/playlist-manager/sources`