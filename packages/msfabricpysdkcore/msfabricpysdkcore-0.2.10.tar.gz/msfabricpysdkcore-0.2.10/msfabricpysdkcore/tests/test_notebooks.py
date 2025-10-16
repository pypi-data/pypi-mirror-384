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

    
    def test_notebooks(self):
            
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        item_id = "9a2edf0f-2318-4179-80d0-1002f3dae7b1"

        notebook_name = "notebook" + datetime.now().strftime("%Y%m%d%H%M%S")

        notebook_w_content = fc.get_notebook(workspace_id, notebook_id=item_id)

        definition = fc.get_notebook_definition(workspace_id, notebook_w_content.id)
        
        self.assertIsNotNone(definition)
        self.assertIn("definition", definition)
        definition = definition["definition"]
        notebook = fc.create_notebook(workspace_id, definition=definition, display_name=notebook_name)
        fc.update_notebook_definition(workspace_id, notebook.id, definition=definition)
        notebook = fc.get_notebook(workspace_id, notebook_id=notebook.id)
        self.assertEqual(notebook.display_name, notebook_name)
        self.assertIsNotNone(notebook.definition)
        
        notebooks = fc.list_notebooks(workspace_id)
        notebook_names = [nb.display_name for nb in notebooks]
        self.assertGreater(len(notebooks), 0)
        self.assertIn(notebook_name, notebook_names)

        nb = fc.get_notebook(workspace_id, notebook_name=notebook_name)
        self.assertIsNotNone(nb.id)
        self.assertEqual(nb.display_name, notebook_name)

        nb2 = fc.update_notebook(workspace_id, notebook_id=nb.id, display_name=f"{notebook_name}2", return_item=True)

        nb = fc.get_notebook(workspace_id, notebook_id=nb.id)
        self.assertEqual(nb.display_name, f"{notebook_name}2")
        self.assertEqual(nb.id, nb2.id)

        status_code = fc.delete_notebook(workspace_id, nb.id)
        self.assertEqual(status_code, 200)