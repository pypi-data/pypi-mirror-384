import configparser
import sys
import threading
import time
from json import JSONDecodeError

import pika
import logging
import json

from pika.exceptions import ConnectionClosedByBroker, AMQPChannelError, AMQPConnectionError
from pikajson.exceptions.need_retry_exception import NeedRetryException

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)
logging.getLogger('pika').setLevel(logging.WARNING)


class PikaConsumer:
    reconnection_timeout = 5

    def __init__(self, handlers, queue, host, port, user, password, max_length=None,
                 prefetch_count=20, heartbeat_timeout=60, wait_queue=None, retry_timeout=0, max_retries=3):
        self._queue = queue
        self._wait_queue = wait_queue
        self._host = host
        self._port = port
        self._user = user
        self._pass = password
        self._terminate = False
        self._handlers = handlers
        self._connection = None
        self._channel = None
        self._max_length = max_length
        self._disconnection_cs = threading.Lock()
        self._active_callbacks = 0
        self._prefetch_count = prefetch_count
        self._active_threads = []
        self._retry_timeout = retry_timeout
        self._max_retries = max_retries
        # Here we will store messages, which are really processed, but the acknowledge wasn't sent
        self._repeatable_messages = []
        self._heartbeat_timeout = heartbeat_timeout


    @classmethod
    def create_from_config(cls, handlers, config_path, config_section='consumer', retry_timeout=0, max_retries=3):
        config = configparser.ConfigParser()
        config.readfp(open(config_path))
        queue = config.get(config_section, "queue")
        host = config.get(config_section, "host")
        port = config.get(config_section, "port")
        user = config.get(config_section, "user")
        password = config.get(config_section, "password")
        max_length = config.get(config_section, "max_length", fallback=None)
        wait_queue = config.get(config_section, "wait_queue", fallback=None)
        return cls(handlers, queue, host, port, user, password, max_length, wait_queue=wait_queue, retry_timeout=retry_timeout, max_retries=max_retries)

    def __del__(self):
        self.terminate()

    def terminate(self):
        self._terminate = True

    def connect(self):
        with self._disconnection_cs:
            logging.info("start connecting on host %s queue %s" % (self._host, self._queue))
            credentials = pika.PlainCredentials(self._user, self._pass)
            parameters = pika.ConnectionParameters(host=self._host, port=self._port, credentials=credentials,
                                                   heartbeat=self._heartbeat_timeout)
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            arguments = None
            if self._max_length is not None:
                arguments = {"x-max-length": int(self._max_length), "x-overflow": "reject-publish"}
            self._channel.basic_qos(prefetch_count=self._prefetch_count)
            self._channel.queue_declare(queue=self._queue, durable=True, arguments=arguments)
            if self._wait_queue is not None:
                arguments = {
                    'x-message-ttl':  int(self._retry_timeout),
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': self._queue
                }
                self._channel.queue_declare(queue=self._wait_queue, durable=True, arguments=arguments)

    def disconnect(self):
        with self._disconnection_cs:
            if self._connection is not None and not self._connection.is_closed:
                logging.info("start server disconnection on host %s queue %s" % (self._host, self._queue))
                try:
                    self._channel.stop_consuming()
                except Exception as ex:
                    logging.error("rabbit stop consuming error: %s" % str(ex),
                                  extra={"queue": self._queue, "host": self._host})
                try:
                    while self._active_callbacks > 0:
                        time.sleep(1)
                    self._connection.close()
                except Exception as ex:
                    logging.error("rabbit disconnect error: %s" % str(ex),
                                  extra={"queue": self._queue, "host": self._host})

    def start(self):
        while not self._terminate:
            try:
                self.connect()
                logging.info("start consuming on host %s queue %s" % (self._host, self._queue))
                self._consuming()
            except ConnectionClosedByBroker as ex:
                if not self._terminate:
                    logging.error("server broke the connection: %s in line %s, reconnecting in %d seconds..." %
                                  (str(sys.exc_info()[-1].tb_lineno), str(ex), self.reconnection_timeout),
                                  extra={"queue": self._queue, "host": self._host})
                    time.sleep(self.reconnection_timeout)
            except AMQPChannelError as ex:
                if not self._terminate:
                    logging.error("caught a channel error in line %s: %s, reconnecting..." %
                                  (str(sys.exc_info()[-1].tb_lineno), str(ex)),
                                  extra={"queue": self._queue, "host": self._host})
            except AMQPConnectionError as ex:
                if not self._terminate:
                    logging.error("connection was closed in line %s: %s, reconnecting in %d seconds..." %
                                  (str(sys.exc_info()[-1].tb_lineno), str(ex), self.reconnection_timeout),
                                  extra={"queue": self._queue, "host": self._host})
                    time.sleep(self.reconnection_timeout)
            except Exception as ex:
                if not self._terminate:
                    logging.error("start error in line %s: %s, restart in %d seconds" %
                                  (str(sys.exc_info()[-1].tb_lineno), str(ex), self.reconnection_timeout),
                                  extra={"queue": self._queue, "host": self._host})
                    time.sleep(self.reconnection_timeout)
            finally:
                self.disconnect()
        logging.info("rabbit consumer terminated on host %s queue %s" % (self._host, self._queue))

    def _consuming(self):
        for message in self._channel.consume(queue=self._queue, inactivity_timeout=5):

            method, properties, body = message
            
            if body is not None:
                self._callback(ch=self._channel, method=method, properties=properties, body=body)

            if self._terminate:
                break

    def _retry(self, body, timeout):
        if self._wait_queue is not None:
            body['retry'] = body.get('retry', 0) + 1
            if self._max_retries >= body['retry']:
                self._channel.basic_publish(
                    exchange='',
                    routing_key=self._wait_queue,
                    body=json.dumps(body),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        expiration=timeout
                    )
                )

    def _callback(self, ch, method, properties, body):
        try:
            self._active_callbacks += 1
            if type(body) is bytes:
                body = body.decode('utf-8')
            message = json.loads(body)
            if "action" in message.keys():
                action = message["action"]
                unique = message["rmq_unique"]
                if action in self._handlers.keys():
                    if unique not in self._repeatable_messages:
                        try:
                            if self._handlers[action](message):
                                try:
                                    ch.basic_ack(delivery_tag=method.delivery_tag)
                                except Exception as ex:
                                    logging.error("cannot send acknowledge: %s" % str(ex))
                                    self._repeatable_messages.append(unique)
                        except NeedRetryException as ex:
                            logging.info("Resubmit required in line %s: %s" % (str(sys.exc_info()[-1].tb_lineno), str(ex)),
                                extra={"queue": self._queue, "body": body, "host": self._host})
                            self._retry(ex.message, ex.timeout)
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logging.error("no such handler: %s" % action)
            else:
                logging.error("wrong message format: no column action")
        except JSONDecodeError as ex:
            logging.error("json decode error in line %s: %s" % (str(sys.exc_info()[-1].tb_lineno), str(ex)))
        except Exception as ex:
            logging.error("rabbit callback error in line %s: %s" % (str(sys.exc_info()[-1].tb_lineno), str(ex)),
                          extra={"queue": self._queue, "body": body, "host": self._host})
        finally:
            self._active_callbacks -= 1
