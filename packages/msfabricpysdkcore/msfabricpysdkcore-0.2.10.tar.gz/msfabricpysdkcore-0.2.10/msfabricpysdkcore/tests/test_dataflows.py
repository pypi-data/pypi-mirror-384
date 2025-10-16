import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_dataflows(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "8bc6f2f1-2ef9-4dc1-ab47-f55aa90e4088"


        resp = fcc.discover_dataflow_parameters(workspace_id, item_id)

        self.assertIsInstance(resp, list)
        self.assertGreater(len(resp), 0)

        for param in resp:
            self.assertIn("type", param)
            self.assertIn("name", param)
            self.assertIn("description", param)
            self.assertIn("isRequired", param)
            self.assertIn("defaultValue", param)

        dataflows = fcc.list_dataflows(workspace_id=workspace_id)
        for dataflow in dataflows:
            if dataflow.id != item_id:
                resp = fcc.delete_dataflow(workspace_id=workspace_id, dataflow_id=dataflow.id)
                self.assertEqual(resp, 200)

        dataflow_definition = fcc.get_dataflow_definition(workspace_id=workspace_id, dataflow_id=item_id)
        self.assertIn("definition", dataflow_definition)
        definition = dataflow_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"dataflow{date_str}"

        dataflow_new = fcc.create_dataflow(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(dataflow_new.display_name, date_str)

        dataflow_get = fcc.get_dataflow(workspace_id=workspace_id, dataflow_id=dataflow_new.id)
        self.assertEqual(dataflow_get.display_name, date_str)

        dataflows = fcc.list_dataflows(workspace_id=workspace_id)
        self.assertEqual(len(dataflows), 2)

        date_str_updated = date_str + "_updated"
        dataflow_updated = fcc.update_dataflow(workspace_id=workspace_id, dataflow_id=dataflow_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(dataflow_updated.display_name, date_str_updated)

        dataflow_updated = fcc.update_dataflow_definition(workspace_id=workspace_id, dataflow_id=dataflow_new.id, definition=definition)
        self.assertEqual(dataflow_updated.status_code, 200)

        for dataflow in dataflows:
            if dataflow.id != item_id:
                resp = fcc.delete_dataflow(workspace_id=workspace_id, dataflow_id=dataflow.id)
                self.assertEqual(resp, 200)







