from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_review.conftest import create_product_and_review


@pytest.mark.asyncio
async def test_update_review_rating(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        UPDATED_RATING = 3

        product_id = await create_product_and_review(client, user, rating=5)

        response = await client.patch(
            f'/reviews/{product_id}',
            json={'rating': UPDATED_RATING},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()['rating'] == UPDATED_RATING

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_review_comment(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        product_id = await create_product_and_review(
            client, user, comment='Comentário original'
        )

        response = await client.patch(
            f'/reviews/{product_id}',
            json={'comment': 'Comentário atualizado'},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()['comment'] == 'Comentário atualizado'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_review_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.patch(
            '/reviews/999',
            json={'rating': 3},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == 'Review not found'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_review_invalid_rating(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        product_id = await create_product_and_review(client, user)

        response = await client.patch(
            f'/reviews/{product_id}',
            json={'rating': 6},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_review_requires_auth(client):
    response = await client.patch('/reviews/999', json={'rating': 3})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
