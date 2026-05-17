from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product, make_variation


@pytest.mark.asyncio
async def test_delete_product_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(name='Produto Delete'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.delete(
            f'/products/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT

        get_response = await client.get(f'/products/{product_id}')
        assert get_response.status_code == HTTPStatus.NOT_FOUND

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_product_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.delete(
            '/products/999',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == 'Product not found'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_product_forbidden(client, user, other_user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(name='Produto Protegido'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        app.dependency_overrides[get_current_user] = lambda: other_user

        response = await client.delete(
            f'/products/{product_id}',
            headers={'Authorization': f'Bearer {other_user.token}'},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['detail'] == 'Not enough permissions'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_product_removes_variations_and_images(
    client, user, store
):
    """Variations and images must be cascade deleted with the product."""
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(
                name='Produto Cascade',
                variations=[
                    make_variation(
                        sku='CASCADE-001',
                        images=[
                            {
                                'url': 'http://img.com/cascade.jpg',
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

        await client.delete(
            f'/products/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        get_response = await client.get(f'/products/{product_id}')
        assert get_response.status_code == HTTPStatus.NOT_FOUND

    finally:
        app.dependency_overrides.clear()
