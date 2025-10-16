import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_tags(self):
        fcc = self.fcc

        tags = fcc.list_tags()

        self.assertIsInstance(tags, list)
        self.assertGreater(len(tags), 0)
        sdk_tag = [tag for tag in tags if tag['displayName'] == 'sdk_tag'][0]
        self.assertIsNotNone(sdk_tag)

        resp = fcc.unapply_tags("05bc5baa-ef02-4a31-ab20-158a478151d3", "a9e59ec1-524b-49b1-a185-37e47dc0ceb9", [sdk_tag["id"]])
        self.assertEqual(resp, 200)
        resp = fcc.apply_tags("05bc5baa-ef02-4a31-ab20-158a478151d3", "a9e59ec1-524b-49b1-a185-37e47dc0ceb9", [sdk_tag["id"]])
        self.assertEqual(resp, 200)


