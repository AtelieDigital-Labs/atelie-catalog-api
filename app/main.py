from fastapi import FastAPI

from app.api.routes import store,auth_test

app = FastAPI()


app.include_router(store.router)
app.include_router(auth_test.router)


@app.get('/')
def read_root():
    return {'message': 'Catalog Service is running'}
