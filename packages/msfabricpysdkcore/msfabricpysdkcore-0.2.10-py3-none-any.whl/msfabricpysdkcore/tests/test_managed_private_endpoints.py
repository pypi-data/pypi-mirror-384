import unittest
from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fc = FabricClientCore()

    def test_workspace_managed_private_endpoints(self):
                    
        fc = self.fc
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        mpes = fc.list_workspace_managed_private_endpoints(workspace_id=workspace_id)

        if len(mpes) > 0:

            for mpe in mpes:
                status_code = fc.delete_workspace_managed_private_endpoint(workspace_id=workspace_id,
                                                                        managed_private_endpoint_id=mpe["id"])
                self.assertEqual(status_code, 200)
            sleep(60)

        mpe = fc.create_workspace_managed_private_endpoint(workspace_id=workspace_id,
                                                           name=f'testmpe{datetime_str}',
                                                           target_private_link_resource_id='/subscriptions/c77cc8fc-43bb-4d44-bdc5-6e20511ed2a8/resourceGroups/fabricdemo/providers/Microsoft.Storage/storageAccounts/publicfabricdemo9039',
                                                           target_subresource_type='dfs',
                                                           request_message='testmessage')

        mpes = fc.list_workspace_managed_private_endpoints(workspace_id=workspace_id)

        self.assertIsNotNone(mpes)
        self.assertGreater(len(mpes), 0)

        mpe2 = fc.get_workspace_managed_private_endpoint(workspace_id=workspace_id,
                                                         managed_private_endpoint_id=mpe["id"])

        self.assertEqual(mpe2["id"], mpe["id"])

        self.assertIsNotNone(mpe2["connectionState"])
        self.assertIn("targetPrivateLinkResourceId", mpe2)
        self.assertEqual(mpe2["targetPrivateLinkResourceId"], "/subscriptions/c77cc8fc-43bb-4d44-bdc5-6e20511ed2a8/resourceGroups/fabricdemo/providers/Microsoft.Storage/storageAccounts/publicfabricdemo9039")

        for _ in range(0, 20):
            if mpe2["connectionState"]["status"] != "Pending":
                sleep(30)
            else:
                status_code = fc.delete_workspace_managed_private_endpoint(workspace_id=workspace_id,
                                                                           managed_private_endpoint_id=mpe["id"])
                self.assertEqual(status_code, 200)
                break
            mpe2 = fc.get_workspace_managed_private_endpoint(workspace_id=workspace_id,
                                                             managed_private_endpoint_id=mpe["id"])

