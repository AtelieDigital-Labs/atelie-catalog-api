from fastapi import FastAPI

from app.api.routes import auth_test, store

app = FastAPI()


app.include_router(store.router)
app.include_router(auth_test.router)


@app.get('/')
def read_root():
    return {'message': 'Catalog Service is running'}
