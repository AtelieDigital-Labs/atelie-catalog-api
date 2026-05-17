from tests.test_product.conftest import make_product


async def create_and_favorite(client, user):
    """cria produto e favorita em um passo."""
    create_response = await client.post(
        '/products/',
        json=make_product(name='Produto Favorito'),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    product_id = create_response.json()['id']

    await client.post(
        f'/favorites/{product_id}',
        headers={'Authorization': f'Bearer {user.token}'},
    )

    return product_id
