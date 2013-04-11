import json
import socket
try:
    import gevent
    import zmq.green as zmq
except ImportError:
    import zmq

from multiprocessing import Process
from zmq.eventloop import ioloop, zmqstream


DEFAULT_ENDPOINT = 'tcp://127.0.0.1:9999'
DEFAULT_PUBSUB = 'tcp://127.0.0.1:9998'


class FeedbackPublisher(Process):
    """Publishes all the feedback received from the various nodes.
    """
    def __init__(self, endpoint=DEFAULT_ENDPOINT,
                 pubsub_endpoint=DEFAULT_PUBSUB,
                 context=None, handler=None):
        Process.__init__(self)
        self.context = context
        self.endpoint = endpoint
        self.pubsub_endpoint = pubsub_endpoint
        self.daemon = True
        self.handler = handler

    def _handler(self, msg):
        if self.handler is not None:
            self.handler(msg)
        self.pub_sock.send_multipart(['feedback', msg[0]])

    def run(self):
        print 'publisher running in a thread'
        self.context = self.context or zmq.Context.instance()
        self.sock = self.context.socket(zmq.PULL)
        self.sock.bind(self.endpoint)
        self.pub_sock = self.context.socket(zmq.PUB)
        self.pub_sock.bind(self.pubsub_endpoint)
        self.loop = ioloop.IOLoop.instance()
        self.stream = zmqstream.ZMQStream(self.sock, self.loop)
        self.stream.on_recv(self._handler)
        self.loop.start()

    def stop(self):
        self.loop.close()


class FeedbackSender(object):
    """Sends feedback
    """
    def __init__(self, endpoint=DEFAULT_ENDPOINT, server=None, context=None):
        self.context = context or zmq.Context.instance()
        self.sock = self.context.socket(zmq.PUSH)
        self.sock.connect(endpoint)
        if server is None:
            server = socket.gethostname()
        self.server = server

    def test_done(self, data):
        data['server'] = self.server
        self.sock.send(json.dumps(data))


class FeedbackSubscriber(Process):
    """Subscribes to a published feedback.
    """
    def __init__(self, pubsub_endpoint=DEFAULT_PUBSUB, handler=None,
                 context=None, **kw):
        Process.__init__(self)
        self.handler = handler
        self.context = context
        self.pubsub_endpoint = pubsub_endpoint
        self.daemon = True
        self.kw = kw

    def _handler(self, msg):
        topic, msg = msg
        msg = json.loads(msg)
        if self.handler is None:
            print msg
        else:
            self.handler(msg, **self.kw)

    def run(self):
        self.context = self.context or zmq.Context.instance()
        self.pub_sock = self.context.socket(zmq.SUB)
        self.pub_sock.connect(self.pubsub_endpoint)
        self.pub_sock.setsockopt(zmq.SUBSCRIBE, b'')
        self.loop = ioloop.IOLoop.instance()
        self.stream = zmqstream.ZMQStream(self.pub_sock, self.loop)
        self.stream.on_recv(self._handler)
        self.loop.start()

    def stop(self):
        self.loop.close()


if __name__ == '__main__':
    print 'Starting subscriber'
    sub = FeedbackSubscriber()
    print 'Listening to events on %r' % sub.pubsub_endpoint
    try:
        sub.run()
    except KeyboardInterrupt:
        sub.stop()
        print 'Bye!'
