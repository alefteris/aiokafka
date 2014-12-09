import asyncio
import socket
import unittest
import uuid

from functools import wraps
from kafka.common import OffsetRequest

from aiokafka.client import connect


__all__ = ['get_open_port', 'KafkaIntegrationTestCase']


def run_until_complete(fun):
    if not asyncio.iscoroutinefunction(fun):
        fun = asyncio.coroutine(fun)

    @wraps(fun)
    def wrapper(test, *args, **kw):
        loop = test.loop
        ret = loop.run_until_complete(
            asyncio.wait_for(fun(test, *args, **kw), 15, loop=loop))
        return ret
    return wrapper


class BaseTest(unittest.TestCase):
    """Base test case for unittests.
    """
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()
        del self.loop


class KafkaIntegrationTestCase(BaseTest):

    def setUp(self):
        self.topic = b'aiokafka_test'
        super().setUp()
        hosts = ['{}:{}'.format(self.server.host, self.server.port)]
        self.client = self.loop.run_until_complete(
            connect(hosts, loop=self.loop))
        self.loop.run_until_complete(
            self.client.ensure_topic_exists(self.topic))
        self._messages = {}

    def tearDown(self):
        self.client.close()
        del self.client
        super().tearDown()

    @asyncio.coroutine
    def current_offset(self, topic, partition):
        offsets, = yield from self.client.send_offset_request(
            [OffsetRequest(topic, partition, -1, 1)])
        return offsets.offsets[0]

    def msgs(self, iterable):
        return [self.msg(x) for x in iterable]

    def msg(self, s):
        if s not in self._messages:
            self._messages[s] = '%s-%s-%s' % (s, self.id(), str(uuid.uuid4()))

        return self._messages[s].encode('utf-8')

    def key(self, k):
        return k.encode('utf-8')


def get_open_port():
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port
