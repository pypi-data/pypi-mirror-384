import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_maps(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "9dcf0419-0f08-4cf4-b282-7a0272d02ff0"

        maps = fcc.list_maps(workspace_id=workspace_id)
        for map in maps:
            if map.id != item_id:
                resp = fcc.delete_map(workspace_id=workspace_id, map_id=map.id)
                self.assertEqual(resp, 200)

        map_definition = fcc.get_map_definition(workspace_id=workspace_id, map_id=item_id)
        self.assertIn("definition", map_definition)
        definition = map_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"map{date_str}"

        map_new = fcc.create_map(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(map_new.display_name, date_str)

        map_get = fcc.get_map(workspace_id=workspace_id, map_id=map_new.id)
        self.assertEqual(map_get.display_name, date_str)

        maps = fcc.list_maps(workspace_id=workspace_id)
        self.assertEqual(len(maps), 2)

        date_str_updated = date_str + "_updated"
        map_updated = fcc.update_map(workspace_id=workspace_id, map_id=map_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(map_updated.display_name, date_str_updated)

        map_updated = fcc.update_map_definition(workspace_id=workspace_id, map_id=map_new.id, definition=definition)
        self.assertEqual(map_updated.status_code, 200)

        for map in maps:
            if map.id != item_id:
                resp = fcc.delete_map(workspace_id=workspace_id, map_id=map.id)
                self.assertEqual(resp, 200)







