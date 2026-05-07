from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product, make_variation


@pytest.mark.asyncio
async def test_get_product_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Get',
                variations=[
                    make_variation(
                        sku='GET-001',
                        color='Azul',
                        size='M',
                        images=[
                            {
                                'url': 'http://img.com/get.jpg',
                                'is_primary': True,
                            }
                        ],
                    )
                ],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED

        product_id = create_response.json()['id']

        response = await client.get(f'/products/{product_id}')

        assert response.status_code == HTTPStatus.OK

        data = response.json()

        assert data['id'] == product_id
        assert data['name'] == 'Produto Get'
        assert data['is_active'] is True
        assert data['store_id'] == store.id
        assert len(data['variations']) == 1

        variation = data['variations'][0]
        assert variation['sku'] == 'GET-001'
        assert variation['color'] == 'Azul'
        assert variation['size'] == 'M'
        assert len(variation['images']) == 1
        assert variation['images'][0]['url'] == 'http://img.com/get.jpg'
        assert variation['images'][0]['is_primary'] is True

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    response = await client.get('/products/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Product not found'


@pytest.mark.asyncio
async def test_get_product_returns_all_variations(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_VARIATIONS = 3

        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Multi Variações',
                variations=[
                    make_variation(sku='VAR-001', color='Azul', size='P'),
                    make_variation(sku='VAR-002', color='Azul', size='M'),
                    make_variation(sku='VAR-003', color='Azul', size='G'),
                ],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED

        product_id = create_response.json()['id']

        response = await client.get(f'/products/{product_id}')

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['variations']) == EXPECTED_VARIATIONS

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_product_does_not_require_auth(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    create_response = await client.post(
        '/products/',
        json=make_product(store.id, name='Produto Público'),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert create_response.status_code == HTTPStatus.CREATED
    product_id = create_response.json()['id']

    # remove só o override do usuário, mantém o override de sessão do client
    del app.dependency_overrides[get_current_user]

    # chama sem usuário autenticado — rota é pública
    response = await client.get(f'/products/{product_id}')
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_get_inactive_product_returns_404(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Inativo'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        patch_response = await client.patch(
            f'/products/{product_id}',
            json={'is_active': False},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert patch_response.status_code == HTTPStatus.OK
        assert patch_response.json()['is_active'] is False

        response = await client.get(f'/products/{product_id}')
        assert response.status_code == HTTPStatus.NOT_FOUND

    finally:
        app.dependency_overrides.clear()
