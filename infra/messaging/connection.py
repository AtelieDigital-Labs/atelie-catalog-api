import pika


def get_connection():

    credentials = pika.PlainCredentials(
        "guest",
        "guest"
    )

    parameters = pika.ConnectionParameters(
        host='127.0.0.1',
        port=5672,
        credentials=credentials,
    )

    return pika.BlockingConnection(parameters)