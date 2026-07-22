from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product, make_variation


@pytest.mark.asyncio
async def test_get_variation_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    EXPECTED_STOCK = 10

    create_response = await client.post(
        '/products/',
        json=make_product(
            name='Produto Variação',
            variations=[
                make_variation(
                    price=89.90,
                    stock=EXPECTED_STOCK,
                    sku='VAR-TEST-001',
                    color='Azul',
                    size='M',
                )
            ],
        ),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert create_response.status_code == HTTPStatus.CREATED
    variation_id = create_response.json()['variations'][0]['id']

    del app.dependency_overrides[get_current_user]  # ← remove só o user

    response = await client.get(f'/products/variations/{variation_id}')

    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert data['id'] == variation_id
    assert data['store_id'] == store.id
    assert data['stock'] == EXPECTED_STOCK
    assert data['sku'] == 'VAR-TEST-001'
    assert data['color'] == 'Azul'
    assert data['size'] == 'M'


@pytest.mark.asyncio
async def test_get_variation_not_found(client):
    response = await client.get('/products/variations/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Variation not found'


@pytest.mark.asyncio
async def test_get_variation_does_not_require_auth(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    create_response = await client.post(
        '/products/',
        json=make_product(name='Produto Público'),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert create_response.status_code == HTTPStatus.CREATED
    variation_id = create_response.json()['variations'][0]['id']

    del app.dependency_overrides[get_current_user]

    response = await client.get(f'/products/variations/{variation_id}')
    assert response.status_code == HTTPStatus.OK
