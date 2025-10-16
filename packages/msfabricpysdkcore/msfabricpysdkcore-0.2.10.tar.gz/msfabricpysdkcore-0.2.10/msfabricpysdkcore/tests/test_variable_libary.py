
import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_variable_librarys(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "0812f094-1a5a-4b2a-aba2-e764af2709ec"

        variable_librarys = fcc.list_variable_libraries(workspace_id=workspace_id)
        for variable_library in variable_librarys:
            if variable_library.id != item_id:
                resp = fcc.delete_variable_library(workspace_id=workspace_id, variable_library_id=variable_library.id)
                self.assertEqual(resp, 200)

        variable_library_definition = fcc.get_variable_library_definition(workspace_id=workspace_id, variable_library_id=item_id)
        self.assertIn("definition", variable_library_definition)
        definition = variable_library_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"variablelibrary{date_str}"

        variable_library_new = fcc.create_variable_library(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(variable_library_new.display_name, date_str)

        variable_library_get = fcc.get_variable_library(workspace_id=workspace_id, variable_library_id=variable_library_new.id)
        self.assertEqual(variable_library_get.display_name, date_str)

        variable_librarys = fcc.list_variable_libraries(workspace_id=workspace_id)
        self.assertEqual(len(variable_librarys), 2)

        date_str_updated = date_str + "_updated"
        variable_library_updated = fcc.update_variable_library(workspace_id=workspace_id, variable_library_id=variable_library_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(variable_library_updated.display_name, date_str_updated)

        variable_library_updated = fcc.update_variable_library_definition(workspace_id=workspace_id, variable_library_id=variable_library_new.id, definition=definition)
        self.assertIn(variable_library_updated.status_code, [200, 202])

        for variable_library in variable_librarys:
            if variable_library.id != item_id:
                resp = fcc.delete_variable_library(workspace_id=workspace_id, variable_library_id=variable_library.id)
                self.assertEqual(resp, 200)







