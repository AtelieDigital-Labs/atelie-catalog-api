import asyncio
import sys

from fastapi import FastAPI

from app.api.routes.auth_test import router as auth_router
from app.api.routes.product import router as product_router
from app.api.routes.store import router as store_router

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

app.include_router(store_router)
app.include_router(auth_router)
app.include_router(product_router)


@app.get('/')
def read_root():
    return {'message': 'Catalog Service is running'}
