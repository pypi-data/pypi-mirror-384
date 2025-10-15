
import pytest
from pikajson.client import PikaPublisher

class TestClient:
    
    @pytest.fixture
    def cls_pika_publisher(self):
        cls_pikaPublisher = PikaPublisher
        return cls_pikaPublisher

    @pytest.fixture
    def pika_publisher(self, connect, readfp, builtins_open, configparser_get):
        pika_publisher = PikaPublisher.create_from_config('config_path')
        return pika_publisher
    
    @pytest.fixture
    def readfp(self, mocker):
        return mocker.patch('configparser.ConfigParser.readfp', return_value=None)
    
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
                'with_declare': 1,
                'with_confirmation': 1
            }

            return conf.get(key)
        return mocker.patch('configparser.ConfigParser.get', new=config)
    
    @pytest.fixture
    def connect(self, mocker):
        return mocker.patch('pikajson.client.PikaPublisher.connect', return_value=True)
    
    @pytest.fixture
    def disconnect(self, mocker):
        return mocker.patch('pikajson.client.PikaPublisher.disconnect', return_value=True)
    
    @pytest.fixture
    def builtins_open(self, mocker):
        mocker.patch('builtins.open', mocker.mock_open(read_data=""))

    @pytest.fixture
    def plain_credentials(self, mocker):
        mock_obj = mocker.MagicMock()
        mocker.patch('pika.PlainCredentials', return_value=mock_obj)
        return mock_obj
    
    @pytest.fixture
    def json_dumps(self, mocker):
        mocker.patch('pikajson.client.json.dumps', return_value="json")
    
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
    def connection_parameters(self, mocker):
        mock_obj = mocker.MagicMock()
        mocker.patch('pika.ConnectionParameters', return_value=mock_obj)
        return mock_obj

    def test_create_from_config(self, cls_pika_publisher, connect, readfp, builtins_open, configparser_get):
        cpp = cls_pika_publisher.create_from_config('config_path')
        assert cpp._queue == 'test'
        assert cpp._host == 'https:\\test.host'
        assert cpp._port == 6400
        assert cpp._user == 'test-user'
        assert cpp._pass == 'test-password'
        assert cpp._max_length == 100
        assert cpp._with_declare == True
        assert cpp._with_confirmation == 1
        assert cpp.connected == False
        assert cpp._connection == None
        assert cpp._channel == None
        connect.assert_called()

    def test_disconnect(self, pika_publisher, blocking_connection):
        bc = blocking_connection
        bc.is_closed = False
        pika_publisher._connection = bc
        pika_publisher.disconnect()
        pika_publisher._connection.close.assert_called()

    def test_disconnect_already_closed(self, pika_publisher, blocking_connection):
        bc = blocking_connection
        bc.is_closed = True
        pika_publisher._connection = bc
        pika_publisher.disconnect()
        pika_publisher._connection.close.assert_not_called()
    
    def test_connect(self, readfp, builtins_open, configparser_get, blocking_connection, plain_credentials, connection_parameters):
        pika_publisher = PikaPublisher.create_from_config('config_path')
        pika_publisher._connection.channel.assert_called()
        pika_publisher._channel.queue_declare.assert_called_with(
            queue='test',
            durable=True,
            arguments= {
                "x-max-length": 100,
                "x-overflow": "reject-publish"
            }
        )
        pika_publisher._channel.confirm_delivery.assert_called()
        assert pika_publisher.connected == True

    def test_connect_max_len_none(self, readfp, builtins_open, configparser_get, blocking_connection, plain_credentials, connection_parameters):
        pika_publisher = PikaPublisher(
            queue='test',
            host='https:\\test.host',
            port=6400,
            user='user',
            password='pass',
            max_length=None,
            with_declare=1,
            with_confirmation=1
        )
        pika_publisher._connection.channel.assert_called()
        pika_publisher._channel.queue_declare.assert_called_with(
            queue='test',
            durable=True,
            arguments=None
        )
        pika_publisher._channel.confirm_delivery.assert_called()
        assert pika_publisher.connected == True

    def test_connect_not_declared(self, readfp, builtins_open, configparser_get, blocking_connection, plain_credentials, connection_parameters):
        pika_publisher = PikaPublisher(
            queue='test',
            host='https:\\test.host',
            port=6400,
            user='user',
            password='pass',
            max_length=None,
            with_declare=0,
            with_confirmation=1
        )
        pika_publisher._connection.channel.assert_called()
        pika_publisher._channel.queue_declare.assert_not_called()
        pika_publisher._channel.confirm_delivery.assert_called()
        assert pika_publisher.connected == True

    def test_connect_not_confirmation(self, readfp, builtins_open, configparser_get, blocking_connection, plain_credentials, connection_parameters):
        pika_publisher = PikaPublisher(
            queue='test',
            host='https:\\test.host',
            port=6400,
            user='user',
            password='pass',
            max_length=None,
            with_declare=0,
            with_confirmation=0
        )
        pika_publisher._connection.channel.assert_called()
        pika_publisher._channel.queue_declare.assert_not_called()
        pika_publisher._channel.confirm_delivery.assert_not_called()
        assert pika_publisher.connected == True

    def test_publish(self, pika_publisher, basic_properties, mocker, json_dumps):
        pika_publisher._channel = mocker.MagicMock()
        message = {
            'test': 'test',
        }
        pika_publisher.publish(message)
        pika_publisher._channel.basic_publish.assert_called_with(
            exchange='',
            routing_key='test',
            body='json',
            properties=basic_properties,
            mandatory=True
        )

    def test__del__(self, pika_publisher, disconnect):
        pika_publisher.__del__()
        disconnect.assert_called()



