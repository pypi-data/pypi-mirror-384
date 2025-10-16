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

    def test_semantic_models(self):
                    
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        semantic_model_name = "semanticmodel" + datetime_str

        semantic_model_w_content = fc.get_semantic_model(workspace_id, semantic_model_name="Table")

        definition = fc.get_semantic_model_definition(workspace_id, semantic_model_w_content.id)

        self.assertIsNotNone(definition)
        self.assertIn("definition", definition)
        definition = definition["definition"]
        semantic_model = fc.create_semantic_model(workspace_id, display_name=semantic_model_name, definition=definition)
        fc.update_semantic_model_definition(workspace_id, semantic_model.id, definition=definition)
        semantic_model = fc.get_semantic_model(workspace_id, semantic_model_id=semantic_model.id)
        self.assertEqual(semantic_model.display_name, semantic_model_name)
        self.assertIsNotNone(semantic_model.definition)
        
        semantic_models = fc.list_semantic_models(workspace_id)
        semantic_model_names = [sm.display_name for sm in semantic_models]
        self.assertGreater(len(semantic_models), 0)
        self.assertIn(semantic_model_name, semantic_model_names)

        sm = fc.get_semantic_model(workspace_id, semantic_model_name=semantic_model_name)
        self.assertIsNotNone(sm.id)
        self.assertEqual(sm.display_name, semantic_model_name)

        sm2 = fc.update_semantic_model(workspace_id, sm.id, display_name=f"u{semantic_model_name}", return_item=True)

        sm2 = fc.get_semantic_model(workspace_id, semantic_model_id=sm2.id)

        self.assertEqual(sm2.display_name, f"u{semantic_model_name}")

        status_code = fc.delete_semantic_model(workspace_id, sm.id)
        self.assertEqual(status_code, 200)