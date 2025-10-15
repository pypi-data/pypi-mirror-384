import unittest
from nexgenomics import ping

class TestWebhook(unittest.TestCase):
    def test_ping(self):
        p = ping("ABC")
        self.assertEqual (p,"Hello, ABC")




