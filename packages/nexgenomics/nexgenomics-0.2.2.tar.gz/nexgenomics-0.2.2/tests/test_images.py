
import unittest
from nexgenomics import images

class TestImages(unittest.TestCase):
    def test_get_images(self):
        for i in images.get_images():
            print (i["title"])




