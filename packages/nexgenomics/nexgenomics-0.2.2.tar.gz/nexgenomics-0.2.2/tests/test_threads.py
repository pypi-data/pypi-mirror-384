import unittest
import dateutil

from nexgenomics import threads

class TestThreads(unittest.TestCase):

    def test_ping(self):
        p = threads.ping()
        self.assertEqual (p["api"], "v0")
        self.assertEqual (p["host"], "nexgenomics.ai")

    def test_new(self):
        p = threads.new(title="AbCdE")
        print (p)

    def test_get_list(self):
        l = threads.get_list()
        for l in l:
            pass
            #print (l.threadid)
            # maybe assert something about the returned threads?

    def test_post_msg(self):
        thr = threads.new(title="test thread")
        msgs = [thr.post_message(f"This is message {x}") for x in range(5)]

        m = thr.get_messages(thr)
        #print (m)

    def test_assistant(self):
        thr = threads.new(title="assistant thread")
        [thr.post_message(f"This is message {x}") for x in range(5)]
        #response = thr.call_assistant()
        response = thr.call_assistant (message="You are a pirate. What are the capitals of Austria and Germany?", assistant=["aa","bb","cc"], context={"q":100,"r":False})
        print (response)
