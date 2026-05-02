from http import HTTPStatus

import pytest

from app.core.security import get_current_user
from app.main import app


@pytest.mark.asyncio
async def test_categories_flow(client, user):
    # Setup do override
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = await client.post(
            '/stores/categories',
            json={'name': 'Crochê'},
            # Note: Como você já deu override no get_current_user,
            # o token no header pode ser qualquer coisa, o FastAPI vai ignorar
            # a validação do JWT e retornar o seu 'user' fake.
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()['name'] == 'Crochê'

    finally:
        # Garante que limpa mesmo se o assert falhar
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_category_duplicate(client, user):
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        # Primeiro cadastro
        await client.post(
            '/stores/categories',
            json={'name': 'Bordado'},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        # Tentativa de duplicata
        response = await client.post(
            '/stores/categories',
            json={'name': 'Bordado'},
            headers={'Authorization': f'Bearer {user.token}'},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json()['detail'] == 'Esta categoria já está cadastrada'
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_store_success(client, category, user):
    # 1. Setup do comportamento falso
    app.dependency_overrides[get_current_user] = lambda: user

    try:
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

        # 2. Execução
        response = await client.post(
            '/stores/',
            json=payload,
            headers={'Authorization': f'Bearer {user.token}'},
        )

        # 3. Verificações
        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data['name'] == 'Ateliê B'
        assert data['address']['street'] == 'Rua A'
        assert data['artisan_id'] == user.id

    finally:
        # 4. Limpeza garantida
        app.dependency_overrides.clear()


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
    # Usando o other_user para testar a negação de acesso
    app.dependency_overrides[get_current_user] = lambda: other_user
    try:
        payload = {'description': 'Tentativa de alteração indevida'}
        response = await client.patch(
            f'/stores/{store.id}',
            json=payload,
            headers={'Authorization': f'Bearer {other_user.token}'},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert 'permissão' in response.json()['detail']
    finally:
        app.dependency_overrides.clear()
