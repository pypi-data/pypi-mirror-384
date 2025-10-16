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



    def test_eventhouses(self):
            
        fcc = self.fc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "5d544ac1-c58d-4d3a-a032-f57dc4b5c2a7"

        eventhouses = fcc.list_eventhouses(workspace_id=workspace_id)
        for eventhouse in eventhouses:
            if eventhouse.id != item_id:
                resp = fcc.delete_eventhouse(workspace_id=workspace_id, eventhouse_id=eventhouse.id)
                self.assertEqual(resp, 200)

        eventhouse_definition = fcc.get_eventhouse_definition(workspace_id=workspace_id, eventhouse_id=item_id)
        self.assertIn("definition", eventhouse_definition)
        definition = eventhouse_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"eventhouse{date_str}"

        eventhouse_new = fcc.create_eventhouse(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(eventhouse_new.display_name, date_str)

        eventhouse_get = fcc.get_eventhouse(workspace_id=workspace_id, eventhouse_id=eventhouse_new.id)
        self.assertEqual(eventhouse_get.display_name, date_str)

        eventhouses = fcc.list_eventhouses(workspace_id=workspace_id)
        self.assertEqual(len(eventhouses), 2)

        date_str_updated = date_str + "_updated"
        eventhouse_updated = fcc.update_eventhouse(workspace_id=workspace_id, eventhouse_id=eventhouse_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(eventhouse_updated.display_name, date_str_updated)

        eventhouse_updated = fcc.update_eventhouse_definition(workspace_id=workspace_id, eventhouse_id=eventhouse_new.id, definition=definition)
        self.assertIn(eventhouse_updated.status_code, [200, 202])

        for eventhouse in eventhouses:
            if eventhouse.id != item_id:
                resp = fcc.delete_eventhouse(workspace_id=workspace_id, eventhouse_id=eventhouse.id)
                self.assertEqual(resp, 200)