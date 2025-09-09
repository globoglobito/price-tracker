# Price Tracker Search API

FastAPI application for managing search terms for price tracking across different websites.

## Features

- **CRUD Operations**: Create, read, update, delete search terms
- **Active/Inactive Management**: Toggle search status
- **Duplicate Prevention**: Unique constraint on search term + website combination
- **Filtering**: List active searches only
- **Pagination**: Support for skip/limit parameters
- **Auto-generated Documentation**: Swagger UI at `/docs`

## API Endpoints

### Health Checks
- `GET /` - Root health check
- `GET /health` - Detailed health status

### Search Management
- `GET /searches` - List all searches (with optional filtering)
- `POST /searches` - Create a new search term
- `GET /searches/{id}` - Get specific search by ID
- `PUT /searches/{id}` - Update a search term
- `DELETE /searches/{id}` - Delete a search term
- `PATCH /searches/{id}/toggle` - Toggle active status

## Quick Start

### Option 1: Kubernetes Deployment (Recommended)

#### 1. Deploy
```bash
# Deploy to Kubernetes (images built via GitHub Actions)
microk8s kubectl apply -f k8s/api-deployment.yaml
microk8s kubectl apply -f k8s/api-service.yaml
```

#### 2. Access the API
- **API Health**: http://localhost:30080/health
- **API Documentation**: http://localhost:30080/docs
- **Search Endpoint**: http://localhost:30080/searches

### Option 2: Local Development (Advanced)

**Note**: The API is designed to run in Kubernetes. Local development is only for advanced debugging.

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Set Environment Variables
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=price_tracker_db
export DB_USER=admin
export DB_PASSWORD=price_tracker_password
```

#### 3. Set up Database Port Forwarding
```bash
# Forward PostgreSQL port from Kubernetes to localhost
microk8s kubectl port-forward service/postgres-service 5432:5432 -n price-tracker &
```

#### 4. Run the API Locally
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Access Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

**Note**: Use `localhost:30080` for Kubernetes deployment (recommended).

### Create a Search Term
```bash
curl -X POST "http://localhost:8000/searches" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Selmer Mark VI",
    "website": "ebay",
    "is_active": true
  }'
```

### List All Searches
```bash
curl "http://localhost:8000/searches"
```

### List Active Searches Only
```bash
curl "http://localhost:8000/searches?active_only=true"
```

### Toggle Search Status
```bash
curl -X PATCH "http://localhost:8000/searches/1/toggle"
```

## Database Schema

The API connects to the `price_tracker.searches` table with the following structure:

```sql
CREATE TABLE price_tracker.searches (
    id SERIAL PRIMARY KEY,
    search_term VARCHAR(200) NOT NULL,
    website VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(search_term, website)
);
```

## Testing

Run the test script to verify API functionality:

```bash
python api/test_api.py
```

## Architecture

```
api/
├── main.py              # FastAPI application
├── database/
│   └── connection.py    # SQLAlchemy database connection
├── models/
│   └── search.py        # SQLAlchemy model
├── schemas/
│   └── search.py        # Pydantic schemas
├── crud/
│   └── search.py        # CRUD operations
└── test_api.py          # API test script
```

## Error Handling

The API includes comprehensive error handling:

- **404 Not Found**: Search term doesn't exist
- **409 Conflict**: Duplicate search term for same website
- **422 Validation Error**: Invalid request data
- **500 Internal Server Error**: Database connection issues

## Future Enhancements

- Authentication and authorization
- Rate limiting
- Search term validation (e.g., minimum length)
- Bulk operations
- Search history tracking 