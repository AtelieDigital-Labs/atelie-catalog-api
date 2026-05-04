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


# GET /products/{id}


@pytest.mark.asyncio
async def test_get_product_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Get',
                variations=[
                    make_variation(
                        sku='GET-001',
                        color='Azul',
                        size='M',
                        images=[
                            {
                                'url': 'http://img.com/get.jpg',
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

        response = await client.get(f'/products/{product_id}')

        assert response.status_code == HTTPStatus.OK

        data = response.json()

        assert data['id'] == product_id
        assert data['name'] == 'Produto Get'
        assert data['is_active'] is True
        assert data['store_id'] == store.id
        assert len(data['variations']) == 1

        variation = data['variations'][0]
        assert variation['sku'] == 'GET-001'
        assert variation['color'] == 'Azul'
        assert variation['size'] == 'M'
        assert len(variation['images']) == 1
        assert variation['images'][0]['url'] == 'http://img.com/get.jpg'
        assert variation['images'][0]['is_primary'] is True

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    response = await client.get('/products/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Product not found'


@pytest.mark.asyncio
async def test_get_product_returns_all_variations(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        EXPECTED_VARIATIONS = 3

        create_response = await client.post(
            '/products/',
            json=make_product(
                store.id,
                name='Produto Multi Variações',
                variations=[
                    make_variation(sku='VAR-001', color='Azul', size='P'),
                    make_variation(sku='VAR-002', color='Azul', size='M'),
                    make_variation(sku='VAR-003', color='Azul', size='G'),
                ],
            ),
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert create_response.status_code == HTTPStatus.CREATED

        product_id = create_response.json()['id']

        response = await client.get(f'/products/{product_id}')

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()['variations']) == EXPECTED_VARIATIONS

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_product_does_not_require_auth(client, user, store):

    app.dependency_overrides[get_current_user] = lambda: user

    create_response = await client.post(
        '/products/',
        json=make_product(store.id, name='Produto Público'),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert create_response.status_code == HTTPStatus.CREATED

    product_id = create_response.json()['id']

    # remove só o override do usuário, mantém o override de sessão do client
    del app.dependency_overrides[get_current_user]

    # chama sem usuário autenticado — rota é pública
    response = await client.get(f'/products/{product_id}')
    assert response.status_code == HTTPStatus.OK


# PATCH /products/{id}


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


# DELETE /products/{id}


@pytest.mark.asyncio
async def test_delete_product_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        create_response = await client.post(
            '/products/',
            json=make_product(store.id, name='Produto Delete'),
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
            json=make_product(store.id, name='Produto Protegido'),
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
                store.id,
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
