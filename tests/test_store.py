from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app


@pytest.mark.asyncio
async def test_categories_flow(client, user):

    # quando alguém pedir o usuário atual, entregue este 'user' aqui
    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.post(
        '/stores/categories',
        json={'name': 'Crochê'},
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json()['name'] == 'Crochê'

    # Limpa após o teste
    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_create_category_duplicate(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    resp1 = await client.post(
        '/stores/categories',
        json={'name': 'Bordado'},
        headers={'Authorization': f'Bearer {user.token}'},
    )
    assert resp1.status_code == HTTPStatus.CREATED

    resp2 = await client.post(
        '/stores/categories',
        json={'name': 'Bordado'},
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert resp2.status_code == HTTPStatus.BAD_REQUEST
    assert resp2.json()['detail'] == 'Esta categoria já está cadastrada'

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_create_store_success(client, category, user):

    app.dependency_overrides[get_current_user] = lambda: user

    payload = {
        'name': 'Ateliê B',
        'description': 'Produtos artesanais',
        'category_id': category.id,
        'image': 'http://foto.jpg',
        'banner': 'http://banner.jpg',
        'address': {
            'street': 'Rua A',
            'number': 333,
            'neighborhood': 'Centro',
            'city': 'Pau dos Ferros',
            'state': 'RN',
            'zip_code': '59000-000',
        },
    }

    response = await client.post(
        '/stores/',
        json=payload,
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['name'] == 'Ateliê B'
    assert data['address']['street'] == 'Rua A'
    assert data['artisan_id'] == user.id

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_create_store_invalid_category(client, user):
    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.post(
        '/stores/',
        json={
            'name': 'Loja Errada',
            'category_id': 9999,
            'address': {
                'street': 'Rua de Teste',
                'number': 123,
                'neighborhood': 'Bairro de Teste',
                'city': 'Cidade',
                'state': 'RN',
                'zip_code': '59000-000',
            },
        },
        headers={'Authorization': f'Bearer {user.token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()['detail'] == 'Categoria informada não existe'

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_list_all_stores(client, store):

    response = await client.get('/stores/')

    assert response.status_code == HTTPStatus.OK
    data = response.json()['stores']
    assert len(data) == 1
    assert data[0]['name'] == store.name
    assert 'category' in data[0]


@pytest.mark.asyncio
async def test_create_store_validation_name_too_short(client, category, user):

    app.dependency_overrides[get_current_user] = lambda: user

    response = await client.post(
        '/stores/',
        json={'name': 'Ab', 'category_id': category.id},
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY  # 422

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_patch_store_profile_success(client, user, store):

    app.dependency_overrides[get_current_user] = lambda: user

    payload = {
        'description': 'Nova biografia do artesão',
        'image': 'http://novo-perfil.jpg',
        'banner': 'http://novo-banner.jpg',
    }

    response = await client.patch(
        f'/stores/{store.id}',
        json=payload,
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert response.status_code == HTTPStatus.OK
    res_json = response.json()
    assert res_json['description'] == 'Nova biografia do artesão'
    assert res_json['image'] == 'http://novo-perfil.jpg'
    assert res_json['banner'] == 'http://novo-banner.jpg'
    assert res_json['name'] == store.name

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_patch_store_address_success(client, user, store):
    app.dependency_overrides[get_current_user] = lambda: user

    new_street = 'Nova Rua Atualizada'
    new_number = 999

    payload = {'address': {'street': new_street, 'number': new_number}}

    response = await client.patch(
        f'/stores/{store.id}',
        json=payload,
        headers={'Authorization': f'Bearer {user.token}'},
    )

    assert response.status_code == HTTPStatus.OK

    res_json = response.json()
    assert res_json['address']['street'] == new_street
    assert res_json['address']['number'] == new_number

    app.dependency_overrides.pop(get_current_user)


@pytest.mark.asyncio
async def test_patch_store_forbidden(client, other_user, store):

    app.dependency_overrides[get_current_user] = lambda: other_user

    payload = {'description': 'Tentativa de alteração indevida'}

    response = await client.patch(
        f'/stores/{store.id}',
        json=payload,
        headers={'Authorization': f'Bearer {other_user.token}'},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert (
        response.json()['detail'] == 'Loja não encontrada ou você não'
        ' possui permissão para editá-la'
    )

    app.dependency_overrides.pop(get_current_user)
