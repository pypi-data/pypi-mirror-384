import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_digital_twin_builder(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "d7260274-8038-44ec-b096-dec1723931d1"

        digital_twin_builder = fcc.list_digital_twin_builders(workspace_id=workspace_id)
        for digital_twin_builder in digital_twin_builder:
            if digital_twin_builder.id != item_id:
                resp = fcc.delete_digital_twin_builder(workspace_id=workspace_id, digital_twin_builder_id=digital_twin_builder.id)
                self.assertEqual(resp, 200)

        digital_twin_builder_definition = fcc.get_digital_twin_builder_definition(workspace_id=workspace_id, digital_twin_builder_id=item_id)
        self.assertIn("definition", digital_twin_builder_definition)
        definition = digital_twin_builder_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"copyjob{date_str}"

        digital_twin_builder_new = fcc.create_digital_twin_builder(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(digital_twin_builder_new.display_name, date_str)

        digital_twin_builder_get = fcc.get_digital_twin_builder(workspace_id=workspace_id, digital_twin_builder_id=digital_twin_builder_new.id)
        self.assertEqual(digital_twin_builder_get.display_name, date_str)

        digital_twin_builder = fcc.list_digital_twin_builders(workspace_id=workspace_id)
        self.assertEqual(len(digital_twin_builder), 2)

        date_str_updated = date_str + "_updated"
        digital_twin_builder_updated = fcc.update_digital_twin_builder(workspace_id=workspace_id, digital_twin_builder_id=digital_twin_builder_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(digital_twin_builder_updated.display_name, date_str_updated)

        digital_twin_builder_updated = fcc.update_digital_twin_builder_definition(workspace_id=workspace_id, digital_twin_builder_id=digital_twin_builder_new.id, definition=definition)
        self.assertIn(digital_twin_builder_updated.status_code, [200,202])

        for digital_twin_builder in digital_twin_builder:
            if digital_twin_builder.id != item_id:
                resp = fcc.delete_digital_twin_builder(workspace_id=workspace_id, digital_twin_builder_id=digital_twin_builder.id)
                self.assertEqual(resp, 200)







