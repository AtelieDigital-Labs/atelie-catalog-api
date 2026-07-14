import asyncio
import sys

from fastapi import FastAPI

from app.api.routes.favorite import router as favorite_router
from app.api.routes.product import router as product_router
from app.api.routes.review import router as review_router
from app.api.routes.store import router as store_router
from app.core.openapi import configure_openapi
from .core.lifespan import lifespan
import app.core.event_table
import app.audit.product_audit  
import app.core.logger 

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

 
app = FastAPI(lifespan=lifespan, root_path="/api/catalog")

API_PREFIX = '/api/v1/catalog'

app.include_router(store_router, prefix=API_PREFIX)
app.include_router(product_router, prefix=API_PREFIX)
app.include_router(favorite_router, prefix=API_PREFIX)
app.include_router(review_router, prefix=API_PREFIX)


configure_openapi(app)


@app.get('/')
def read_root():
    return {'message': 'Catalog Service is running'}
