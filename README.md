# Real Estate Agency System

A FastAPI application backed by MongoDB to manage clients and their properties.

## Requirements

- Python 3.13+
- MongoDB running on `localhost:27017` (or set `MONGO_URL` environment variable)

## Installation

1. Install dependencies:
   ```bash
   uv sync
   # or
   pip install fastapi uvicorn motor pydantic email-validator
   ```

## Running the App

```bash
uv run python main.py
# or
python main.py
```

The API will be available at `http://localhost:8000`.
Documentation is available at `http://localhost:8000/docs`.

## API Endpoints

- `POST /clients/`: Create a new client.
- `GET /clients/`: List all clients.
- `GET /clients/{id}`: Get a specific client.
- `POST /clients/{id}/properties/`: Add a property to a client.

## Example Usage

Create a client:
```bash
curl -X POST "http://localhost:8000/clients/" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "email": "john@example.com", "phone": "1234567890"}'
```

Add a property:
```bash
curl -X POST "http://localhost:8000/clients/{CLIENT_ID}/properties/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Beach House", "address": "123 Ocean Dr", "city": "Miami", "price": 500000}'
```
