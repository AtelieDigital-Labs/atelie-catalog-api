from tests.test_product.conftest import make_product


def make_review(**kwargs):
    base = {
        'rating': 5,
        'comment': 'Produto excelente!',
    }
    base.update(kwargs)
    return base


async def create_product_and_review(client, user, store, **kwargs):
    """Helper — cria produto e avaliação em um passo."""
    create_response = await client.post(
        '/products/',
        json=make_product(store.id),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    product_id = create_response.json()['id']

    await client.post(
        f'/reviews/{product_id}',
        json=make_review(**kwargs),
        headers={'Authorization': f'Bearer {user.token}'},
    )

    return product_id
