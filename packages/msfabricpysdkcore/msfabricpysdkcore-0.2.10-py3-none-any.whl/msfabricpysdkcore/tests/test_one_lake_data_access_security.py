import unittest
from dotenv import load_dotenv
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fc = FabricClientCore()

    def test_one_lake_data_access_security(self):

        fc = self.fc

        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        item_id = "63023672-df30-4bfb-adce-f292beb357af"

        resp = fc.list_data_access_roles(workspace_id=workspace_id, item_id=item_id)
        self.assertEqual(len(resp), 2)

        roles = resp[0]
        etag = resp[1]

        role1 = roles[1]

        self.assertIn('members', role1)
        self.assertIn('fabricItemMembers', role1['members'])
        self.assertGreater(len(role1['members']['fabricItemMembers']), 0)
        self.assertIn('itemAccess', role1['members']['fabricItemMembers'][0])

        item_access = role1["members"]["fabricItemMembers"][0]['itemAccess']
        item_access_old = list(item_access)
        if 'ReadAll' in item_access:
            item_access = ['Read', 'Write', 'Execute']
        else:
            item_access.append('ReadAll')

        role1["members"]["fabricItemMembers"][0]['itemAccess'] = item_access
        roles[1] = role1

        resp = fc.create_or_update_data_access_roles(workspace_id=workspace_id, 
                                                     item_id=item_id, 
                                                     data_access_roles=roles, 
                                                     etag_match={"If-Match":etag})


        resp = fc.list_data_access_roles(workspace_id=workspace_id, item_id=item_id)
        self.assertEqual(len(resp), 2)

        roles = resp[0]
        etag = resp[1]

        role1 = roles[1]

        self.assertIn('members', role1)
        self.assertIn('fabricItemMembers', role1['members'])
        self.assertGreater(len(role1['members']['fabricItemMembers']), 0)
        self.assertIn('itemAccess', role1['members']['fabricItemMembers'][0])

        item_access = role1["members"]["fabricItemMembers"][0]['itemAccess']
        self.assertNotEqual(item_access, item_access_old)