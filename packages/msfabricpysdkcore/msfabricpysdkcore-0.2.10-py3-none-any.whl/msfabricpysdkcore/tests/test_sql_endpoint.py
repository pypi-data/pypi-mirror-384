import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_sql_endpoint(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "d21012a1-f306-4cf1-a21b-f8ae55c17642"

        audit_settings = fcc.get_sql_endpoint_audit_settings(workspace_id=workspace_id, sql_endpoint_id=item_id)

        self.assertIn("state", audit_settings)
        self.assertIn("retentionDays", audit_settings)
        self.assertIn("auditActionsAndGroups", audit_settings)

        respo = fcc.update_sql_endpoint_audit_settings(workspace_id=workspace_id, sql_endpoint_id=item_id,
                                               state="Enabled", retention_days=10)
        self.assertEqual(respo.status_code, 200)

        actionsandgroups = ["SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP",  "FAILED_DATABASE_AUTHENTICATION_GROUP",  "BATCH_COMPLETED_GROUP"]

        respo = fcc.set_sql_endpoint_audit_actions_and_groups(workspace_id=workspace_id, sql_endpoint_id=item_id,
                                                      set_audit_actions_and_groups_request=actionsandgroups)
        self.assertEqual(respo.status_code, 200)
        