import pytest
from pikajson.server import PikaConsumer
from pikajson.exceptions.need_retry_exception import NeedRetryException
import json

class TestServer:

    @pytest.fixture
    def configparser_get(self, mocker):
        def config(self, section, key, fallback=0): 
            conf = {
                'queue': 'test',
                'host': 'https:\\test.host',
                'port': 6400,
                'user': 'test-user',
                'password': 'test-password',
                'max_length': 100,
                'wait_queue': 'wait_test',
            }

            return conf.get(key)

        return mocker.patch('configparser.ConfigParser.get', new=config)
    
    @pytest.fixture
    def pika_consumer(self):
        pika_consumer = PikaConsumer(
            handlers={},
            queue='test',
            host='local',
            port=6400,
            user='user',
            password='pass',
            max_length=100,
            prefetch_count=20,
            heartbeat_timeout=60,
            wait_queue='wait_test',
            retry_timeout=30,
            max_retries=3
        )
        return pika_consumer
    
    @pytest.fixture
    def cls_pika_consumer(self):
        cls_pika_consumer = PikaConsumer
        return cls_pika_consumer
    
    @pytest.fixture
    def readfp(self, mocker):
        return mocker.patch('configparser.ConfigParser.readfp', return_value=None)
    
    @pytest.fixture
    def connection_parameters(self, mocker):
        mock_obj = mocker.MagicMock()
        mocker.patch('pika.ConnectionParameters', return_value=mock_obj)
        return mock_obj
    
    @pytest.fixture
    def plain_credentials(self, mocker):
        mock_obj = mocker.MagicMock()
        mocker.patch('pika.PlainCredentials', return_value=mock_obj)
        return mock_obj
    
    @pytest.fixture
    def blocking_connection(self, mocker):
        mock_obj = mocker.MagicMock()
        mocker.patch('pika.BlockingConnection', return_value=mock_obj)
        return mock_obj
    
    @pytest.fixture
    def basic_properties(self, mocker):
        mock_obj = mocker.MagicMock()
        mocker.patch('pika.BasicProperties', return_value=mock_obj)
        return mock_obj
    
    @pytest.fixture
    def builtins_open(self, mocker):
        mocker.patch('builtins.open', mocker.mock_open(read_data=""))

    @pytest.fixture
    def time_sleep(self, pika_consumer, mocker):
        def set_active_callback_zero(sec):
            pika_consumer._active_callbacks = 0
        mocker.patch('time.sleep', new=set_active_callback_zero)

    @pytest.fixture
    def json_dumps(self, mocker):
        mocker.patch('json.dumps', return_value='json')

    @pytest.fixture
    def json_loads(self, mocker):
        mocker.patch('json.loads', return_value={'action': 'test', 'rmq_unique': 'rmq_unique'})

    @pytest.fixture
    def connect(self, mocker):
        return mocker.patch('pikajson.server.PikaConsumer.connect', return_value=True)
    
    @pytest.fixture
    def consuming(self, mocker):
        return mocker.patch('pikajson.server.PikaConsumer._consuming', return_value=True)
    
    @pytest.fixture
    def disconnect(self, mocker):
        return mocker.patch('pikajson.server.PikaConsumer.disconnect', return_value=True)
    
    @pytest.fixture
    def disconnect_stop(self, mocker, pika_consumer):
        def stop(*args):
            pika_consumer._terminate = True
        return mocker.patch('pikajson.server.PikaConsumer.disconnect', new=stop)
    
    def test_create_from_config(self, cls_pika_consumer, readfp, builtins_open, configparser_get):
        cpc = cls_pika_consumer.create_from_config(
            'callback',
            'config_path'
        )
        assert cpc._queue == 'test'
        assert cpc._wait_queue == 'wait_test'
        assert cpc._host == 'https:\\test.host'
        assert cpc._port == 6400
        assert cpc._user == 'test-user'
        assert cpc._pass == 'test-password'
        assert cpc._max_length == 100
        assert cpc._connection == None
        assert cpc._channel == None
        assert cpc._terminate == False
        assert cpc._handlers == 'callback'
        assert cpc._active_callbacks == 0
        assert cpc._active_threads == []
        assert cpc._retry_timeout == 0
        assert cpc._max_retries == 3

    def test_terminate(self, pika_consumer):
        pika_consumer.terminate()
        assert pika_consumer._terminate == True

    def test__del__(self, pika_consumer):
        pika_consumer.__del__()
        assert pika_consumer._terminate == True
    
    def test_connect(self, pika_consumer, plain_credentials, connection_parameters, blocking_connection):
        pika_consumer.connect()
        pika_consumer._connection.channel.assert_called_with()
        pika_consumer._channel.basic_qos.assert_called_with(prefetch_count=20)
        pika_consumer._channel.queue_declare.assert_called()
        pika_consumer._channel.queue_declare(
            queue='wait_test',
            durable=True,
            arguments={
                'x-message-ttl': 0,
                'x-dead-letter-exchange': 'test',
                'x-dead-letter-routing-key': 'test'
            }
        )

    def test_conect_max_len_none(self, pika_consumer, plain_credentials, connection_parameters, blocking_connection):
        pika_consumer._wait_queue = None
        pika_consumer._max_length = None
        pika_consumer.connect()
        pika_consumer._connection.channel.assert_called_with()
        pika_consumer._channel.basic_qos.assert_called_with(prefetch_count=20)
        pika_consumer._channel.queue_declare.assert_called_with(
            queue='test',
            durable=True,
            arguments=None
        )

    def test_connect_not_wait_queue(self, pika_consumer, plain_credentials, connection_parameters, blocking_connection):
        pika_consumer._wait_queue = None
        pika_consumer.connect()
        pika_consumer._connection.channel.assert_called_with()
        pika_consumer._channel.basic_qos.assert_called_with(prefetch_count=20)
        pika_consumer._channel.queue_declare.assert_called_with(
            queue='test',
            durable=True,
            arguments={
                "x-max-length": 100,
                "x-overflow": "reject-publish"
            }
        )

    def test_disconnect(self, pika_consumer, mocker):
        pika_consumer._connection = mocker.MagicMock(is_closed=False)
        pika_consumer._channel = mocker.MagicMock()
        pika_consumer.disconnect()
        pika_consumer._channel.stop_consuming.assert_called()
        pika_consumer._connection.close.assert_called()

    def test_disconnect_already_disconnected(self, pika_consumer, mocker):
        pika_consumer._connection = mocker.MagicMock(is_closed=True)
        pika_consumer._channel = mocker.MagicMock()
        pika_consumer.disconnect()
        pika_consumer._channel.stop_consuming.assert_not_called()
        pika_consumer._connection.close.assert_not_called()

    def test_disconnect_with_active_callbacks(self, pika_consumer, mocker, time_sleep):
        pika_consumer._connection = mocker.MagicMock(is_closed=False)
        pika_consumer._channel = mocker.MagicMock()
        pika_consumer._active_callbacks = 1
        pika_consumer.disconnect()
        pika_consumer._channel.stop_consuming.assert_called()
        pika_consumer._connection.close.assert_called()

    def test_consuming(self, pika_consumer, mocker):
        def consume(**kwarg):
            return {('method','properties','message')}
        pika_consumer._channel = mocker.MagicMock(consume=consume)
        pika_consumer._callback = mocker.MagicMock()
        pika_consumer.disconnect = mocker.MagicMock()
        pika_consumer._consuming()
        pika_consumer._callback.assert_called_with(
            ch=pika_consumer._channel,
            method='method',
            properties='properties',
            body='message'
        )

    def test_consuming_with_terminate(self, pika_consumer, mocker):
        def consume(**kwarg):
            return {('method','properties','message')}
        pika_consumer._channel = mocker.MagicMock(consume=consume)
        pika_consumer._callback = mocker.MagicMock()
        pika_consumer.disconnect = mocker.MagicMock()
        pika_consumer._terminate = True
        pika_consumer._consuming()

    def test_retry(self, pika_consumer, mocker, basic_properties, json_dumps):
        body = {'retry': 1}
        pika_consumer._channel = mocker.MagicMock()
        pika_consumer._retry(body, 100)
        pika_consumer._channel.basic_publish.assert_called_with(
            exchange='',
            routing_key='wait_test',
            body='json',
            properties=basic_properties
        )

    def test_retry_not_wait_queue(self, pika_consumer, mocker, basic_properties, json_dumps):
        body = {'retry': 1}
        pika_consumer._wait_queue = None
        pika_consumer._channel = mocker.MagicMock()
        pika_consumer._retry(body, 100)
        pika_consumer._channel.basic_publish.assert_not_called()

    def test_retry_limit(self, pika_consumer, mocker, basic_properties):
        body = {'retry': 1000}
        pika_consumer._channel = mocker.MagicMock()
        pika_consumer._retry(body, 100)
        pika_consumer._channel.basic_publish.assert_not_called()

    def test_callback(self, pika_consumer, mocker, json_loads):
        ch = mocker.MagicMock()
        method = mocker.MagicMock(delivery_tag='test')
        body = json.dumps({
            'action': 'test',
            'rmq_unique': 'rmq_unique'
        })
        callback = mocker.MagicMock()
        pika_consumer._handlers['test'] = callback
        pika_consumer._callback(ch, method, None, body)
        pika_consumer._handlers['test'].assert_called_with({'action': 'test','rmq_unique': 'rmq_unique'})
        ch.basic_ack.assert_called_with(delivery_tag='test')
        assert pika_consumer._active_callbacks == 0

    def test_callback_with_no_action(self, pika_consumer, mocker, json_loads):
        ch = mocker.MagicMock()
        method = mocker.MagicMock(delivery_tag='test')
        body = json.dumps({
            'action': 'test',
            'rmq_unique': 'rmq_unique'
        })
        pika_consumer._callback(ch, method, None, body)
        ch.basic_ack.assert_not_called()
        assert pika_consumer._active_callbacks == 0

    def test_callback_with_not_rmq_unique(self, pika_consumer, mocker, json_loads):
        ch = mocker.MagicMock()
        method = mocker.MagicMock(delivery_tag='test')
        body = json.dumps({
            'action': 'test',
            'rmq_unique': 'rmq_unique'
        })
        callback = mocker.MagicMock()
        pika_consumer._handlers['test'] = callback
        pika_consumer._repeatable_messages.append('rmq_unique')
        pika_consumer._callback(ch, method, None, body)
        pika_consumer._handlers['test'].assert_not_called()
        ch.basic_ack.assert_called_with(delivery_tag='test')
        assert pika_consumer._active_callbacks == 0

    def test_callback_with_need_retry_exception(self, pika_consumer, mocker, json_loads):
        ch = mocker.MagicMock()
        method = mocker.MagicMock(delivery_tag='test')
        body = json.dumps({
            'action': 'test',
            'rmq_unique': 'rmq_unique'
        })
        def callback(*args):
            raise NeedRetryException(message='test', timeout=100)

        pika_consumer._handlers['test'] = callback
        pika_consumer._retry = mocker.MagicMock()
        pika_consumer._callback(ch, method, None, body)
        
        pika_consumer._retry.assert_called_with('test', 100)
        assert pika_consumer._active_callbacks == 0
    
    def test_start(self, pika_consumer, connect, consuming, disconnect_stop):
        pika_consumer.start()
        connect.assert_called()
        consuming.assert_called()

    def test_start_terminated(self, pika_consumer, connect, consuming, disconnect):
        pika_consumer._terminate = True
        pika_consumer.start()
        connect.assert_not_called()
        consuming.assert_not_called()
        disconnect.assert_not_called()

