from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app

# helpers


def make_variation(**kwargs):
    base = {
        'price': 10,
        'weight': 1,
        'length': 1,
        'width': 1,
        'height': 1,
        'stock': 1,
        'images': [],
    }
    base.update(kwargs)
    return base


def make_product(store_id, **kwargs):
    base = {
        'name': 'Produto Teste',
        'description': 'descrição teste',
        'store_id': store_id,
        'variations': [make_variation()],
    }
    base.update(kwargs)
    return base


# POST /products/


@pytest.mark.asyncio
async def test_create_product_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_PRICE = 10.5

        payload = make_product(
            store.id,
            name='Produto Teste',
            description='Descrição teste',
            variations=[
                make_variation(
                    price=EXPECTED_PRICE,
                    weight=1.0,
                    length=10,
                    width=5,
                    height=2,
                    sku='SKU123',
                    stock=10,
                    color='Azul',
                    size='M',
                    images=[
                        {'url': 'http://img.com/1.jpg', 'is_primary': True}
                    ],
                )
            ],
        )

        response = await client.post(
            '/products/',
            json=payload,
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CREATED

        data = response.json()

        assert data['name'] == 'Produto Teste'
        assert data['description'] == 'Descrição teste'
        assert data['is_active'] is True
        assert len(data['variations']) == 1

        variation = data['variations'][0]
        assert variation['price'] == EXPECTED_PRICE
        assert variation['sku'] == 'SKU123'
        assert variation['color'] == 'Azul'
        assert variation['size'] == 'M'
        assert len(variation['images']) == 1
        assert variation['images'][0]['url'] == 'http://img.com/1.jpg'
        assert variation['images'][0]['is_primary'] is True

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_product_store_not_found(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/products/',
            json=make_product(store_id=999),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json()['detail'] == (
            'Loja não encontrada ou sem permissão'
        )

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_product_store_belongs_to_another_user(
    client, user, other_user, store
):
    app.dependency_overrides[get_current_user] = lambda: other_user

    try:
        response = await client.post(
            '/products/',
            json=make_product(store.id),
            headers={'Authorization': f'Bearer {other_user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_product_without_variations(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/products/',
            json=make_product(store.id, variations=[]),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()['variations'] == []

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_product_name_too_short(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/products/',
            json=make_product(store.id, name='AB'),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_product_negative_price(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                variations=[make_variation(price=-1)],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_product_duplicate_sku(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                variations=[
                    make_variation(sku='SKU-IGUAL'),
                    make_variation(sku='SKU-IGUAL'),
                ],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert response.json()['detail'] == 'SKU já cadastrado'

    finally:
        app.dependency_overrides.clear()


# GET /products/


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
async def test_list_products_filter_by_name(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_COUNT = 2

        for name in ['Camiseta Azul', 'Camiseta Verde', 'Calça Preta']:
            await client.post(
                '/products/',
                json=make_product(store.id, name=name),
                headers={'Authorization': f'Bearer {user.token}'},
            )

        response = await client.get('/products/?name=Camiseta')

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
    response = await client.get('/products/?name=AB')

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


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
