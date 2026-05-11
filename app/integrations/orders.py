class OrdersClient:
    """
    Integration with atelie-orders-api.

    TODO: implement when orders-api is ready.

    Example of future implementation:
        async def validate_purchase(user_id: str, product_id: int) -> bool:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'{settings.ORDERS_API_URL}/orders/validate',
                    params={
                        'user_id': user_id,
                        'product_id': product_id,
                        'status': 'delivered',
                    },
                )
                return response.json()['is_valid']
    """

    @staticmethod
    async def validate_purchase(user_id: str, product_id: int) -> bool:
        """
        Validates if user has purchased and received the product.
        Returns True until orders-api integration is implemented.
        """
        return True  # ← placeholder
