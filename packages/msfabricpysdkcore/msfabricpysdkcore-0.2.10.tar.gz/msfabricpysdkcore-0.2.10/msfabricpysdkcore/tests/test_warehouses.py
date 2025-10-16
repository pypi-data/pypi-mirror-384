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

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        self.item_name = "testitem" + datetime_str
        self.item_type = "Notebook"


    def test_warehouses(self):

        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        warehouse1 = f"wh{datetime_str}"
        warehouse = fc.create_warehouse(workspace_id, display_name=warehouse1)
        self.assertIsNotNone(warehouse.id)

        warehouses = fc.list_warehouses(workspace_id)
        warehouse_names = [wh.display_name for wh in warehouses]
        self.assertGreater(len(warehouses), 0)
        self.assertIn(warehouse1, warehouse_names)

        warehouse = fc.get_warehouse(workspace_id, warehouse_name=warehouse1)
        self.assertIsNotNone(warehouse.id)
        self.assertEqual(warehouse.display_name, warehouse1)

        warehouse2 = fc.update_warehouse(workspace_id, warehouse.id, display_name=f"{warehouse1}2", return_item=True)
        warehouse = fc.get_warehouse(workspace_id, warehouse_id=warehouse.id)
        self.assertEqual(warehouse.display_name, f"{warehouse1}2")
        self.assertEqual(warehouse.id, warehouse2.id)

        status_code = fc.delete_warehouse(workspace_id, warehouse.id)
        self.assertEqual(status_code, 200)
    
    def test_other_warehouse_stuff(self):
        fcc = self.fc
        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "e4655180-815b-4339-984b-213a23524685"

        resp = fcc.get_warehouse_connection_string(workspace_id, item_id)

        self.assertIn('connectionString', resp)
        self.assertIsInstance(resp['connectionString'], str)


        resp = fcc.list_warehouse_restore_points(workspace_id, item_id)
        self.assertGreater(len(resp), 0)
        for rp in resp:
            if rp['id'] != "1760452482000" and rp['creationMode'] != 'SystemCreated':
                rp_to_delete = rp['id']
                break

        resp = fcc.create_warehouse_restore_point(workspace_id, item_id, "my second restore point", wait_for_completion=False)
        
        self.assertIn(resp.status_code, [200, 201, 202])

        resp = fcc.get_warehouse_restore_point(workspace_id, item_id, "1760452482000")
        self.assertEqual(resp, {
            'id': '1760452482000',
            'displayName': 'my first restore point',
            'description': '',
        })

        resp = fcc.update_warehouse_restore_point(workspace_id, item_id, rp_to_delete, description="updated description")

        self.assertEqual(resp['description'], "updated description")
        resp = fcc.delete_warehouse_restore_point(workspace_id, item_id, rp_to_delete)
        self.assertEqual(resp.status_code, 200)

        resp = fcc.restore_warehouse_to_restore_point(workspace_id, item_id, "1760452482000")
        self.assertIn(resp.status_code, [200, 201, 202])

        audit_settings = fcc.get_warehouse_sql_audit_settings(workspace_id=workspace_id, warehouse_id=item_id)

        self.assertIn("state", audit_settings)
        self.assertIn("retentionDays", audit_settings)
        self.assertIn("auditActionsAndGroups", audit_settings)

        respo = fcc.update_warehouse_sql_audit_settings(workspace_id=workspace_id, warehouse_id=item_id,
                                               state="Enabled", retention_days=10)
        self.assertEqual(respo.status_code, 200)

        actionsandgroups = ["SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP",  "FAILED_DATABASE_AUTHENTICATION_GROUP",  "BATCH_COMPLETED_GROUP"]

        respo = fcc.set_warehouse_audit_actions_and_groups(workspace_id=workspace_id, warehouse_id=item_id,
                                                      set_audit_actions_and_groups_request=actionsandgroups)
        self.assertEqual(respo.status_code, 200)
        


if __name__ == "__main__":
    unittest.main()