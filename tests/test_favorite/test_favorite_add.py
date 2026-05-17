from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product


@pytest.mark.asyncio
async def test_add_favorite_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(name='Produto Favorito'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.post(
            f'/favorites/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CREATED

        data = response.json()
        assert data['product_id'] == product_id
        assert data['user_id'] == user.id

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_add_favorite_product_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/favorites/999',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == 'Product not found'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_add_favorite_inactive_product(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(name='Produto Inativo'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        await client.patch(
            f'/products/{product_id}',
            json={'is_active': False},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.post(
            f'/favorites/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_add_favorite_duplicate(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(name='Produto Duplicado'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        await client.post(
            f'/favorites/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.post(
            f'/favorites/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()['detail'] == 'Product already favorited'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_add_favorite_requires_auth(client, store, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(name='Produto Sem Auth'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

    finally:
        app.dependency_overrides.clear()

    response = await client.post(f'/favorites/{product_id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
