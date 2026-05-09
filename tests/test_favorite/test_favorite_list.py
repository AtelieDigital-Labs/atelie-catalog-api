from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_favorite.conftest import create_and_favorite
from tests.test_product.conftest import make_product


@pytest.mark.asyncio
async def test_list_favorites_empty(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.get(
            '/favorites/',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {'favorites': []}

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_favorites_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 2

        for name in ['Produto A', 'Produto B']:
            create_response = await client.post(
                '/products/',
                json=make_product(store.id, name=name),
                headers={'Authorization': f'Bearer {user.token}'},
            )

            assert create_response.status_code == HTTPStatus.CREATED
            product_id = create_response.json()['id']

            await client.post(
                f'/favorites/{product_id}',
                headers={'Authorization': f'Bearer {user.token}'},
            )

        response = await client.get(
            '/favorites/',
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['favorites']) == EXPECTED_COUNT

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_favorites_requires_auth(client):
    response = await client.get('/favorites/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_list_favorites_only_current_user(
    client, user, other_user, store
):
    """Each user sees only their own favorites."""
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        await create_and_favorite(client, user, store)

        app.dependency_overrides[get_current_user] = lambda: other_user

        response = await client.get(
            '/favorites/',
            headers={'Authorization': f'Bearer {other_user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {'favorites': []}

    finally:
        app.dependency_overrides.clear()
