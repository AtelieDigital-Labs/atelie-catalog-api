from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product
from tests.test_review.conftest import make_review


@pytest.mark.asyncio
async def test_create_review_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Avaliado'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.post(
            f'/reviews/{product_id}',
            json=make_review(rating=5, comment='Excelente!'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CREATED

        data = response.json()
        assert data['product_id'] == product_id
        assert data['user_id'] == user.id
        RATING = 5
        assert data['rating'] == RATING
        assert data['comment'] == 'Excelente!'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_without_comment(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Sem Comentário'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.post(
            f'/reviews/{product_id}',
            json=make_review(rating=4, comment=None),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()['comment'] is None

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_product_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/reviews/999',
            json=make_review(),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == 'Product not found'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_inactive_product(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Inativo'),
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
            f'/reviews/{product_id}',
            json=make_review(),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_duplicate(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Duplicado'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        await client.post(
            f'/reviews/{product_id}',
            json=make_review(),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.post(
            f'/reviews/{product_id}',
            json=make_review(),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()['detail'] == (
            'You have already reviewed this product'
        )

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_invalid_rating(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Rating Inválido'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

        response = await client.post(
            f'/reviews/{product_id}',
            json=make_review(rating=6),  # ← acima do máximo
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_review_requires_auth(client, store, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED
        product_id = create_response.json()['id']

    finally:
        app.dependency_overrides.clear()

    response = await client.post(
        f'/reviews/{product_id}',
        json=make_review(),
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
