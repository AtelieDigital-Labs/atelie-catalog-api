from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product
from tests.test_review.conftest import create_product_and_review, make_review


@pytest.mark.asyncio
async def test_list_reviews_empty(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    create_response = await client.post(
        '/products/',
        json=make_product(name='Produto Sem Avaliação'),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert create_response.status_code == HTTPStatus.CREATED
    product_id = create_response.json()['id']

    del app.dependency_overrides[get_current_user]  # ← remove só o user

    response = await client.get(f'/reviews/{product_id}')

    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert data['reviews'] == []
    assert data['total'] == 0
    assert data['average_rating'] == 0.0


@pytest.mark.asyncio
async def test_list_reviews_success(client, user, other_user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    EXPECTED_TOTAL = 2
    EXPECTED_AVERAGE = 4.0

    create_response = await client.post(
        '/products/',
        json=make_product(name='Produto Avaliado'),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert create_response.status_code == HTTPStatus.CREATED
    product_id = create_response.json()['id']

    await client.post(
        f'/reviews/{product_id}',
        json=make_review(rating=5),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    app.dependency_overrides[get_current_user] = lambda: other_user

    await client.post(
        f'/reviews/{product_id}',
        json=make_review(rating=3),
        headers={'Authorization': f'Bearer {other_user.token}'},
    )

    del app.dependency_overrides[get_current_user]  # ← remove só o user

    response = await client.get(f'/reviews/{product_id}')

    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert data['total'] == EXPECTED_TOTAL
    assert data['average_rating'] == EXPECTED_AVERAGE


@pytest.mark.asyncio
async def test_list_reviews_product_not_found(client):
    response = await client.get('/reviews/999')
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_list_reviews_does_not_require_auth(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    product_id = await create_product_and_review(client, user)

    del app.dependency_overrides[get_current_user]  # ← remove só o user

    response = await client.get(f'/reviews/{product_id}')
    assert response.status_code == HTTPStatus.OK
