from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_categories_flow(client):

    response = await client.post('/stores/categories', json={'name': 'Crochê'})
    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['name'] == 'Crochê'

    response_dup = await client.post(
        '/stores/categories', json={'name': 'Crochê'}
    )
    assert response_dup.status_code == HTTPStatus.BAD_REQUEST

    response_list = await client.get('/stores/categories')
    assert response_list.status_code == HTTPStatus.OK
    assert len(response_list.json()['categories']) >= 1


@pytest.mark.asyncio
async def test_create_store_success(client, category):

    payload = {
        'name': 'Ateliê B',
        'description': 'Produtos artesanais',
        'category_id': category.id,
        'image': 'http://foto.jpg',
        'banner': 'http://banner.jpg',
    }

    response = await client.post('/stores/', json=payload)

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['name'] == 'Ateliê B'
    assert data['category']['name'] == category.name
    assert data['artisan_id'] == '1'


@pytest.mark.asyncio
async def test_create_store_invalid_category(client):

    response = await client.post(
        '/stores/', json={'name': 'Loja Errada', 'category_id': 9999}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Categoria informada não existe'


@pytest.mark.asyncio
async def test_list_all_stores(client, store):

    response = await client.get('/stores/')

    assert response.status_code == HTTPStatus.OK
    data = response.json()['stores']
    assert len(data) == 1
    assert data[0]['name'] == store.name
    assert 'category' in data[0]


@pytest.mark.asyncio
async def test_create_store_validation_name_too_short(client, category):

    response = await client.post(
        '/stores/', json={'name': 'Ab', 'category_id': category.id}
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY  # 422
