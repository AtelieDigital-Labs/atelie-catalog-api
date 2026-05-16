import asyncio
import sys

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes.favorite import router as favorite_router
from app.api.routes.product import router as product_router
from app.api.routes.review import router as review_router
from app.api.routes.store import router as store_router

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

API_PREFIX = "/api/v1/catalog"

app.include_router(store_router, prefix=API_PREFIX)
app.include_router(product_router, prefix=API_PREFIX)
app.include_router(favorite_router, prefix=API_PREFIX)
app.include_router(review_router, prefix=API_PREFIX)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title='Ateliê Catalog API',
        version='1.0.0',
        routes=app.routes,
    )

    openapi_schema['components']['securitySchemes'] = {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
    }

    for path in openapi_schema['paths'].values():
        for method in path.values():
            method['security'] = [{'BearerAuth': []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.get('/')
def read_root():
    return {'message': 'Catalog Service is running'}
