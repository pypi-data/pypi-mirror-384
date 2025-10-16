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

    def test_lakehouse(self):

        lakehouse2 = "lh2" + datetime.now().strftime("%Y%m%d%H%M%S")
        lakehouse3 = "lh3" + datetime.now().strftime("%Y%m%d%H%M%S")

        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        lhs = self.fc.list_lakehouses(workspace_id=workspace_id, with_properties=True)
        lh = [lh_ for lh_ in lhs if lh_.display_name == "lakelhousewlabels"][0]
        tables = lh.list_tables()
        table_names = [t["name"] for t in tables]
        self.assertIn("dimension_customer", table_names)

        lakehouse = self.fc.get_item(workspace_id=workspace_id, item_name="lakelhousewlabels", item_type="Lakehouse")
        self.assertIsNotNone(lakehouse.properties)
        lakehouse_id = lakehouse.id
        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        table_name = f"table{date_str}"


        status_code = self.fc.load_table(workspace_id=workspace_id, lakehouse_id=lakehouse_id, table_name=table_name, 
                                         path_type="File", relative_path="Files/to_share/dimension_customer.csv")

        self.assertEqual(status_code, 202)

        # Run on demand table maintenance
        table_name_maintenance = "dimension_customer"

        execution_data = {
            "tableName": table_name_maintenance,
            "optimizeSettings": {
            "vOrder": True,
            "zOrderBy": [
                "CustomerKey",
            ]
            },
            "vacuumSettings": {
            "retentionPeriod": "7:01:00:00"
            }
        }
        
        response = self.fc.run_on_demand_table_maintenance(workspace_id=workspace_id, lakehouse_id=lakehouse_id, 
                                                           execution_data = execution_data,
                                                           job_type = "TableMaintenance", wait_for_completion = False)
        self.assertIn(response.status_code, [200, 202])

        table_list = self.fc.list_tables(workspace_id=workspace_id, lakehouse_id=lakehouse_id)
        table_names = [table["name"] for table in table_list]

        self.assertIn(table_name, table_names)

        fc = self.fc

        lakehouse = fc.create_lakehouse(workspace_id=workspace_id, display_name=lakehouse2)
        self.assertIsNotNone(lakehouse.id)

        lakehouses = fc.list_lakehouses(workspace_id)
        lakehouse_names = [lh.display_name for lh in lakehouses]
        self.assertGreater(len(lakehouse_names), 0)
        self.assertIn(lakehouse2, lakehouse_names)

        lakehouse2 = fc.get_lakehouse(workspace_id=workspace_id, lakehouse_id=lakehouse.id)
        self.assertEqual(lakehouse.id, lakehouse2.id)

        sleep(20)
        lakehouse2 = fc.update_lakehouse(workspace_id=workspace_id, lakehouse_id=lakehouse.id, display_name=lakehouse3, return_item=True)
        self.assertEqual(lakehouse2.display_name, lakehouse3)

        id = lakehouse2.id

        lakehouse2 = fc.get_lakehouse(workspace_id=workspace_id, lakehouse_name=lakehouse3)
        self.assertEqual(lakehouse2.id, id)

        status_code = fc.delete_lakehouse(workspace_id=workspace_id, lakehouse_id=lakehouse.id)
        self.assertEqual(status_code, 200)