import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientAdmin

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fca = FabricClientAdmin()
                  
    def test_admin_api(self):
        fca = self.fca

        sdk_tag = [tag for tag in fca.list_tags() if tag["displayName"] == "sdk_tag_temp"]
        if len(sdk_tag) > 0:
            sdk_tag = sdk_tag[0]
            resp = fca.delete_tag(tag_id=sdk_tag["id"])
            self.assertEqual(resp, 200)
      
        new_tags = [{"displayName": "sdk_tag_temp"}]
        resp = fca.bulk_create_tags(create_tags_request=new_tags)
        self.assertEqual(len(resp["tags"]), 1)
        resp = resp["tags"][0]
        self.assertEqual(resp["displayName"], "sdk_tag_temp")

        sdk_tag = [tag for tag in fca.list_tags() if tag["displayName"] == "sdk_tag_temp"]
        self.assertEqual(len(sdk_tag), 1)
        sdk_tag = sdk_tag[0]

        self.assertIsNotNone(sdk_tag["id"])

        resp = fca.update_tag(tag_id=sdk_tag["id"], display_name="sdk_tag_updated")
        self.assertIsNotNone(resp["id"])
        self.assertEqual(resp["displayName"], "sdk_tag_updated")


        resp = fca.delete_tag(tag_id=resp["id"])
        self.assertEqual(resp, 200)

        sdk_tag = [tag for tag in fca.list_tags() if tag["displayName"] == "sdk_tag_temp"]
        self.assertEqual(len(sdk_tag), 0)



