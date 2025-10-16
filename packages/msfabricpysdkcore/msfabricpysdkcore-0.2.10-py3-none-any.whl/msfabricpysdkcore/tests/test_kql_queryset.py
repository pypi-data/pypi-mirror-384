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
    
    def test_kql_querysets(self):

        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        kql_queryset_name = "kqlqueryset12"
        kqlq_w_content = fc.get_kql_queryset(workspace_id, kql_queryset_name=kql_queryset_name)

        definition = fc.get_kql_queryset_definition(workspace_id, kqlq_w_content.id)
        self.assertIsNotNone(definition)
        self.assertIn("definition", definition)
        definition = definition["definition"]

        self.assertIsNotNone(kqlq_w_content.id)
        self.assertEqual(kqlq_w_content.display_name, kql_queryset_name)

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        kql_queryset_new = "kqlq" + datetime_str

        kqlq = fc.create_kql_queryset(workspace_id, definition=definition, display_name=kql_queryset_new)
        self.assertIsNotNone(kqlq.id)
        self.assertEqual(kqlq.display_name, kql_queryset_new)

        fc.update_kql_queryset_definition(workspace_id, kqlq.id, definition=definition)
        kqlq = fc.get_kql_queryset(workspace_id, kqlq.id)
        self.assertEqual(kqlq.display_name, kql_queryset_new)
        self.assertIsNotNone(kqlq.definition)

        kqlqs = fc.list_kql_querysets(workspace_id)
        kqlq_names = [kql.display_name for kql in kqlqs]
        self.assertGreater(len(kqlqs), 0)
        self.assertIn(kql_queryset_new, kqlq_names)

        kqlq = fc.get_kql_queryset(workspace_id, kql_queryset_name=kql_queryset_new)
        self.assertIsNotNone(kqlq.id)
        self.assertEqual(kqlq.display_name, kql_queryset_new)

        kqlq2 = fc.update_kql_queryset(workspace_id, kql_queryset_id=kqlq.id, display_name=f"{kql_queryset_new}2", return_item=True)

        kqlq = fc.get_kql_queryset(workspace_id, kql_queryset_id=kqlq.id)
        self.assertEqual(kqlq.display_name, f"{kql_queryset_new}2")
        self.assertEqual(kqlq.id, kqlq2.id)

        status_code = fc.delete_kql_queryset(workspace_id, kqlq.id)
        self.assertEqual(status_code, 200)