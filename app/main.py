import asyncio
import sys

from fastapi import FastAPI

from app.api.routes.favorite import router as favorite_router
from app.api.routes.product import router as product_router
from app.api.routes.review import router as review_router
from app.api.routes.store import router as store_router
from app.core.openapi import configure_openapi

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

API_PREFIX = '/api/v1/catalog'

app.include_router(store_router, prefix=API_PREFIX)
app.include_router(product_router, prefix=API_PREFIX)
app.include_router(favorite_router, prefix=API_PREFIX)
app.include_router(review_router, prefix=API_PREFIX)


configure_openapi(app)


@app.get('/')
def read_root():
    return {'message': 'Catalog Service is running'}
