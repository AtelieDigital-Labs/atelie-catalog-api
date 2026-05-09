from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_favorite.conftest import create_and_favorite


@pytest.mark.asyncio
async def test_remove_favorite_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        product_id = await create_and_favorite(client, user, store)

        response = await client.delete(
            f'/favorites/{product_id}',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_remove_favorite_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.delete(
            '/favorites/999',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == 'Favorite not found'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_remove_favorite_requires_auth(client):
    response = await client.delete('/favorites/999')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
