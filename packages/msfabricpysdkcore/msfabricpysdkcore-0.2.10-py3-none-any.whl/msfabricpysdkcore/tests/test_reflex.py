import unittest
from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

# class TestFabricClientCore(unittest.TestCase):

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fc = FabricClientCore()

   
    def test_reflex(self):

        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")

        reflex_name = "reflex" + datetime_str

        reflex = fc.create_reflex(workspace_id, display_name=reflex_name)
        self.assertEqual(reflex.display_name, reflex_name)

        reflexes = fc.list_reflexes(workspace_id)
        reflex_names = [ref.display_name for ref in reflexes]
        self.assertGreater(len(reflexes), 0)
        self.assertIn(reflex_name, reflex_names)


        ref = fc.get_reflex(workspace_id, reflex_name=reflex_name)
        self.assertIsNotNone(ref.id)
        self.assertEqual(ref.display_name, reflex_name)

        ref2 = fc.update_reflex(workspace_id, ref.id, display_name=f"{reflex_name}2", return_item=True)

        ref = fc.get_reflex(workspace_id, reflex_id=ref.id)
        self.assertEqual(ref.display_name, f"{reflex_name}2")
        self.assertEqual(ref.id, ref2.id)

        response = fc.update_reflex_definition(workspace_id, reflex_id=ref.id, definition=ref.definition)
        self.assertIn(response.status_code, [200, 202])

        definition = fc.get_reflex_definition(workspace_id, reflex_id=ref.id)
        self.assertIn("definition", definition)
        self.assertIn("parts", definition["definition"])
        self.assertGreaterEqual(len(definition["definition"]["parts"]), 2)

        status_code = fc.delete_reflex(workspace_id, ref.id)
        self.assertEqual(status_code, 200)

