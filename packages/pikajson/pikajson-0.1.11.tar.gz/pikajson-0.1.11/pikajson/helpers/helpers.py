
import pika

def get_rmq_count(user, password, host, port, queue):
    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    res = channel.queue_declare(
        queue=queue,
        durable=True,
        exclusive=False,
        auto_delete=False,
        passive=True
    )
    count = res.method.message_count
    channel.close()
    connection.close()
    return count