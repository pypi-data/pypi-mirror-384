import os
import random
import string
import threading
import time

from pikajson.client import PikaPublisher
from pikajson.server import PikaConsumer


class PerformanceTest:

    def __init__(self, wait_time=0.1, action='test', messages_count=100, clients_count=10):
        self.terminate = False
        self.server = None
        self.server_thread = None
        self.client_threads = []
        self.clients = []
        self.clients_timings = []
        self.wait_time = wait_time
        self.action = action
        self.messages_count = messages_count
        self.clients_count = clients_count
        self.server_messages = []
        self.clients_messages = {}
        self.server_work_time = 0
        self.server_termination_time = 0
        self.server_start_time = time.time()

    def test_server(self, message):
        time.sleep(random.randint(1, 10)/10)
        print(message["test"])
        self.server_messages.append(message)
        return True

    def test_waiting(self, message):
        time.sleep(self.wait_time)
        self.server_messages.append(message)
        return True

    def test_threading(self, message):
        thread = threading.Thread(target=self.test_waiting, args=(message,))
        thread.daemon = True
        thread.start()
        return True

    def create_server(self):
        path = os.path.dirname(os.path.abspath(__file__))
        self.server = PikaConsumer.create_from_config({"test": self.test_server,
                                                       "test_waiting": self.test_waiting,
                                                       "test_threading": self.test_threading},
                                                       path + '/configs/consumer.ini')

    def start_server(self):
        self.server_start_time = time.time()
        if self.server is not None:
            self.server_thread = threading.Thread(target=self.server.start)
            self.server_thread.daemon = True
            self.server_thread.start()

    def stop_server(self):
        if self.server is not None and self.server_thread is not None:
            start_time = time.time()
            self.server.terminate()
            self.server_thread.join()
            self.server_work_time = time.time() - self.server_start_time
            self.server_termination_time = time.time() - start_time

    def client_sending(self, number):
        self.clients_messages[number] = []
        path = os.path.dirname(os.path.abspath(__file__))
        client = PikaPublisher.create_from_config(path + '/configs/publisher.ini')
        self.clients.append(client)
        i = 0
        while i < self.messages_count:
            i += 1
            message = "%d_%d" % (number, i)
            start_time = time.time()
            client.publish({"action": self.action, "test": message}, mandatory=False)
            self.clients_timings.append(time.time()-start_time)
            self.clients_messages[number].append(message)

    def start_clients(self):
        i = 0
        while i < self.clients_count:
            i += 1
            client_thread = threading.Thread(target=self.client_sending, args=(i, ))
            client_thread.daemon = True
            client_thread.start()
            self.client_threads.append(client_thread)

    def wait_for_clients(self):
        for thread in self.client_threads:
            thread.join()
