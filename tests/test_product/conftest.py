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


def make_product(**kwargs):
    base = {
        'name': 'Produto Teste',
        'description': 'descrição teste',
        'variations': [make_variation()],
    }
    base.update(kwargs)
    return base
