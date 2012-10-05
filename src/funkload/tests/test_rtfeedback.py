import unittest
import time

from funkload import rtfeedback
import zmq


class TestFeedback(unittest.TestCase):

    def test_feedback(self):

        context = zmq.Context.instance()

        pub = rtfeedback.FeedbackPublisher(context=context)
        pub.start()

        msgs = []

        def _msg(msg):
            msgs.append(msg)

        sub = rtfeedback.FeedbackSubscriber(handler=_msg, context=context)
        sub.start()

        sender = rtfeedback.FeedbackSender(context=context)

        for i in range(10):
            sender.test_done({'result': 'success'})

        time.sleep(.1)
        self.assertEqual(len(msgs), 10)
