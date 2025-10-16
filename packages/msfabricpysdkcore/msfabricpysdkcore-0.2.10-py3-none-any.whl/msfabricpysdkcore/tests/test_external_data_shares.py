import unittest
from dotenv import load_dotenv
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fc = FabricClientCore()

    def test_external_data_shares(self):
        
        fc = self.fc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "82c01e0c-4cee-4a62-9806-870699ced699"

        recipient = {
            "userPrincipalName": "lisa4@fabrikam.com"
        }
        paths=["Files/to_share"]

        resp = fc.create_external_data_share(workspace_id, item_id, paths, recipient)
        self.assertIsNotNone(resp)
        self.assertIn('id', resp)


        get = fc.get_external_data_share(workspace_id, item_id, resp['id'])
        self.assertIsNotNone(get)
        self.assertEqual(get['id'], resp['id'])


        resp = fc.list_external_data_shares_in_item(workspace_id, item_id)
        self.assertGreater(len(resp), 0)

        data_share_ids = [ds['id'] for ds in resp]
        self.assertIn(get['id'], data_share_ids)


        resp = fc.revoke_external_data_share(workspace_id, item_id, get['id'])
        self.assertEqual(resp, 200)

        get2 = fc.get_external_data_share(workspace_id, item_id, get['id'])
        self.assertIsNotNone(get2)
        
        self.assertEqual(get['id'], get2['id'])
        self.assertEqual(get2['status'], 'Revoked')


