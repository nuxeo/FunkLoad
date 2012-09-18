import json
import zmq
import threading
from zmq.eventloop import ioloop, zmqstream


DEFAULT_ENDPOINT = 'tcp://127.0.0.1:9999'
DEFAULT_PUBSUB = 'tcp://127.0.0.1:9998'


class FeedbackPublisher(threading.Thread):
    """Publishes all the feedback received from the various nodes.
    """
    def __init__(self, endpoint=DEFAULT_ENDPOINT,
                 pubsub_endpoint=DEFAULT_PUBSUB):
        threading.Thread.__init__(self)
        self.context = zmq.Context.instance()
        self.sock = self.context.socket(zmq.PULL)
        self.sock.bind(endpoint)
        self.pub_sock = self.context.socket(zmq.PUB)
        self.pub_sock.bind(pubsub_endpoint)
        self.loop = ioloop.IOLoop()
        self.stream = zmqstream.ZMQStream(self.sock, self.loop)
        self.stream.on_recv(self._handler)
        self.daemon = True

    def _handler(self, msg):
        self.pub_sock.send(msg[0])

    def run(self):
        self.loop.start()

    def stop(self):
        self.loop.close()


class FeedbackSender(object):
    """Sends feedback
    """
    def __init__(self, endpoint=DEFAULT_ENDPOINT, server=''):
        self.context = zmq.Context.instance()
        self.sock = self.context.socket(zmq.PUSH)
        self.sock.connect(self.endpoint)
        self.server = server

    def test_done(self, data):
        data['server'] = self.server
        self.sock.send(json.dumps(data))


class FeedbackSubscriber(threading.Thread):
    """Subscribes to a published feedback.
    """
    def __init__(self, pubsub_endpoint=DEFAULT_PUBSUB, handler=None):
        threading.Thread.__init__(self)
        self.context = zmq.Context.instance()
        self.pub_sock = self.context.socket(zmq.SUB)
        self.pub_sock.connect(pubsub_endpoint)
        self.loop = ioloop.IOLoop()
        self.handler = handler
        self.stream = zmqstream.ZMQStream(self.pub_sock, self.loop)
        self.stream.on_recv(self._handler)
        self.daemon = True

    def _handler(self, msg):
        msg = json.loads(msg[0])
        if handler is None:
            print msg
        else:
            self.handler(msg)

    def run(self):
        self.loop.start()

    def stop(self):
        self.loop.close()


if __name__ == '__main__':
    print 'Starting subscriber'
    sub = FeedbackSubscriber()
    try:
        sub.run()
    except KeyboardInterrupt:
        print 'Bye!'
