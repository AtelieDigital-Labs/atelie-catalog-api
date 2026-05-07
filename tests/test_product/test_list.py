from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app
from tests.test_product.conftest import make_product, make_variation


@pytest.mark.asyncio
async def test_list_products_empty(client):
    response = await client.get('/products/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'products': []}


@pytest.mark.asyncio
async def test_list_products_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 2

        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Um'),
            headers={'Authorization': f'Bearer {user.token}'},
        )
        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Dois'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_only_active(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 1

        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Ativo'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

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

        response = await client.get('/products/')

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['products']) == EXPECTED_COUNT
        assert response.json()['products'][0]['name'] == 'Produto Ativo'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_by_q(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 2

        for name in ['Camiseta Azul', 'Camiseta Verde', 'Calça Preta']:
            await client.post(
                '/products/',
                json=make_product(store.id, name=name),
                headers={'Authorization': f'Bearer {user.token}'},
            )

        response = await client.get('/products/?q=Camiseta')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT
        assert all('Camiseta' in p['name'] for p in data['products'])

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_by_store(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto da Loja'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get(f'/products/?store_id={store.id}')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == 1
        assert data['products'][0]['name'] == 'Produto da Loja'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_name_too_short(client):
    response = await client.get('/products/?q=AB')

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_products_filter_by_min_price(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 1

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Barato',
                variations=[make_variation(price=30)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Caro',
                variations=[make_variation(price=200)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/?min_price=100')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT
        assert data['products'][0]['name'] == 'Produto Caro'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_by_max_price(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 1

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Barato',
                variations=[make_variation(price=50)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Caro',
                variations=[make_variation(price=200)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/?max_price=100')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT
        assert data['products'][0]['name'] == 'Produto Barato'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_by_price_range(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 1

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Barato',
                variations=[make_variation(price=30)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Medio',
                variations=[make_variation(price=100)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Caro',
                variations=[make_variation(price=200)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/?min_price=50&max_price=150')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT
        assert data['products'][0]['name'] == 'Produto Medio'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_by_category(client, user, store, category):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 1

        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto da Categoria'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get(f'/products/?category_id={category.id}')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT
        assert data['products'][0]['name'] == 'Produto da Categoria'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_filter_combined(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 1

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Camiseta Barata',
                variations=[make_variation(price=50)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Camiseta Cara',
                variations=[make_variation(price=200)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Calça Barata',
                variations=[make_variation(price=50)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/?q=Camiseta&max_price=100')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data['products']) == EXPECTED_COUNT
        assert data['products'][0]['name'] == 'Camiseta Barata'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_sort_by_price_asc(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Caro',
                variations=[make_variation(price=200)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Barato',
                variations=[make_variation(price=30)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/?sort=price_asc')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        prices = [
            p['variations'][0]['price']
            for p in data['products']
            if p['variations']
        ]
        assert prices == sorted(prices)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_sort_by_newest(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Antigo'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Novo'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        response = await client.get('/products/?sort=newest')

        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert data['products'][0]['name'] == 'Produto Novo'

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_pagination(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        TOTAL_PRODUCTS = 5
        PAGE_SIZE = 2

        for i in range(TOTAL_PRODUCTS):
            await client.post(
                '/products/',
                json=make_product(store.id, name=f'Produto {i}'),
                headers={'Authorization': f'Bearer {user.token}'},
            )

        response_p1 = await client.get(
            f'/products/?limit={PAGE_SIZE}&offset=0'
        )
        response_p2 = await client.get(
            f'/products/?limit={PAGE_SIZE}&offset={PAGE_SIZE}'
        )

        assert response_p1.status_code == HTTPStatus.OK
        assert response_p2.status_code == HTTPStatus.OK

        assert len(response_p1.json()['products']) == PAGE_SIZE
        assert len(response_p2.json()['products']) == PAGE_SIZE

        ids_p1 = {p['id'] for p in response_p1.json()['products']}
        ids_p2 = {p['id'] for p in response_p2.json()['products']}
        assert ids_p1.isdisjoint(ids_p2)

    finally:
        app.dependency_overrides.clear()
