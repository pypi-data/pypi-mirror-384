# Psycopg2Logger
Psycopg2Logger is made to work with https://github.com/larswise/pgquerymon and is a logging library that captures PostgreSQL database queries from psycopg2 and transmits them via TCP to the monitoring application in real-time. It provides detailed SQL query logging with parameter interpolation, execution duration tracking. The logger is optimized for development use with connection pooling, reflection caching, compiled regex patterns, and async logging to minimize performance impact on your application. **Do not run this in production; this is intended for development only.**

## Installation

Install the package via pip:

```bash
pip install psycopg2logger
```

## Usage

### For FastAPI Applications

```python
from fastapi import FastAPI
from psycopg2logger.middleware import SQLInterceptorMiddleware

app = FastAPI()

# Add the middleware to your FastAPI application
app.add_middleware(Psycopg2InterceptorMiddleware)

@app.get("/example")
async def example_endpoint():
    # Your database logic here
    return {"message": "Example endpoint"}

# Run your FastAPI application
# uvicorn main:app --reload
```

## Monitoring Application

To view the captured SQL queries, you'll need the companion monitoring application [pgquerymon](https://github.com/larswise/pgquerymon) which provides a real-time dashboard for analyzing your database interactions.

## Features

- **Real-time SQL logging** with parameter interpolation
- **Execution duration tracking** for performance analysis
- **Intelligent caller detection** to identify source business logic
- **High-performance design** with connection pooling and caching
- **Async logging** to prevent blocking your application
- **Support for FastAPI applications**
- **Configurable performance settings** for different use cases

