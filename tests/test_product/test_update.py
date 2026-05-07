from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product, make_variation


@pytest.mark.asyncio
async def test_update_product_name(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Nome Original'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.patch(
            f'/products/{product_id}',
            json={'name': 'Nome Atualizado'},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()['name'] == 'Nome Atualizado'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_product_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.patch(
            '/products/999',
            json={'name': 'Qualquer'},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == 'Product not found'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_product_forbidden(client, user, other_user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Protegido'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        app.dependency_overrides[get_current_user] = lambda: other_user

        response = await client.patch(
            f'/products/{product_id}',
            json={'name': 'Hackeado'},
            headers={'Authorization': f'Bearer {other_user.token}'},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['detail'] == 'Not enough permissions'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_product_variations_and_images(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_VARIATIONS = 2
        EXPECTED_IMAGES = 2
        UPDATED_PRICE = 20
        NEW_VARIATION_STOCK = 15

        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Original',
                variations=[
                    make_variation(
                        sku='SKU-PATCH-1',
                        images=[
                            {
                                'url': 'http://img.com/old.jpg',
                                'is_primary': True,
                            }
                        ],
                    )
                ],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED

        product = create_response.json()
        product_id = product['id']
        variation_id = product['variations'][0]['id']
        image_id = product['variations'][0]['images'][0]['id']

        response = await client.patch(
            f'/products/{product_id}',
            json={
                'name': 'Produto Atualizado',
                'variations': [
                    {
                        'id': variation_id,
                        'price': UPDATED_PRICE,
                        'weight': 2,
                        'length': 2,
                        'width': 2,
                        'height': 2,
                        'stock': 10,
                        'sku': 'SKU-PATCH-1-UPDATED',
                        'images': [
                            {
                                'id': image_id,
                                'url': 'http://img.com/updated.jpg',
                                'is_primary': True,
                            },
                            {
                                'url': 'http://img.com/new.jpg',
                                'is_primary': False,
                            },
                        ],
                    },
                    {
                        'price': 30,
                        'weight': 3,
                        'length': 3,
                        'width': 3,
                        'height': 3,
                        'stock': 15,
                        'sku': 'SKU-PATCH-2',
                        'images': [],
                    },
                ],
            },
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK

        data = response.json()

        assert data['name'] == 'Produto Atualizado'
        assert len(data['variations']) == EXPECTED_VARIATIONS

        updated_variation = next(
            v for v in data['variations'] if v['id'] == variation_id
        )

        assert updated_variation['price'] == UPDATED_PRICE
        assert updated_variation['sku'] == 'SKU-PATCH-1-UPDATED'
        assert len(updated_variation['images']) == EXPECTED_IMAGES

        updated_image = next(
            img for img in updated_variation['images'] if img['id'] == image_id
        )
        assert updated_image['url'] == 'http://img.com/updated.jpg'

        new_variation = next(
            v for v in data['variations'] if v['sku'] == 'SKU-PATCH-2'
        )
        assert new_variation['stock'] == NEW_VARIATION_STOCK

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_product_remove_variation(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_VARIATIONS = 1

        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                variations=[
                    make_variation(sku='VAR-RM-1'),
                    make_variation(sku='VAR-RM-2'),
                ],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.patch(
            f'/products/{product_id}',
            json={
                'variations': [
                    {
                        'price': 99,
                        'weight': 1,
                        'length': 1,
                        'width': 1,
                        'height': 1,
                        'stock': 1,
                        'sku': 'VAR-RM-ONLY',
                        'images': [],
                    }
                ]
            },
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['variations']) == EXPECTED_VARIATIONS

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_product_duplicate_sku(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        await client.post(
            '/products/',
            json=make_product(
                store.id,
                variations=[make_variation(sku='SKU-EXISTENTE')],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                variations=[make_variation(sku='SKU-PARA-ATUALIZAR')],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.patch(
            f'/products/{product_id}',
            json={
                'variations': [
                    {
                        'price': 10,
                        'weight': 1,
                        'length': 1,
                        'width': 1,
                        'height': 1,
                        'stock': 1,
                        'sku': 'SKU-EXISTENTE',
                        'images': [],
                    }
                ]
            },
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()['detail'] == 'SKU already exists'

    finally:
        app.dependency_overrides.clear()
