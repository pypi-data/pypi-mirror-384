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

   
    def test_kql_dashboards(self):
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        kql_dash = fc.get_kql_dashboard(workspace_id, kql_dashboard_name='dashboard1')
        kql_dash_orig_id = kql_dash.id


        kql_dash_name = "testdash" + datetime_str

        kql_dash = fc.create_kql_dashboard(display_name=kql_dash_name, workspace_id=workspace_id)
        self.assertEqual(kql_dash.display_name, kql_dash_name)

        definition_orig = fc.get_kql_dashboard_definition(workspace_id, kql_dash_orig_id)
        definition_orig = definition_orig["definition"]
        self.assertIsNotNone(definition_orig)

        definition = fc.update_kql_dashboard_definition(workspace_id, kql_dash.id, definition=definition_orig)

        self.assertIsNotNone(definition)

        kql_dashs = fc.list_kql_dashboards(workspace_id)

        kql_dash_names = [kqld.display_name for kqld in kql_dashs]
        self.assertGreater(len(kql_dashs), 0)
        self.assertIn(kql_dash_name, kql_dash_names)
        self.assertIn('dashboard1', kql_dash_names)

        kql_dash2 = fc.get_kql_dashboard(workspace_id, kql_dashboard_name=kql_dash_name)
        self.assertIsNotNone(kql_dash2.id)
        self.assertEqual(kql_dash2.display_name, kql_dash_name)

        new_name = kql_dash_name+"2"
        kql_dash3 = fc.update_kql_dashboard(workspace_id, kql_dash.id, display_name=new_name, return_item=True)

        self.assertEqual(kql_dash3.display_name, new_name)
        self.assertEqual(kql_dash.id, kql_dash3.id)

        resp_code = fc.delete_kql_dashboard(workspace_id, kql_dash3.id)
        self.assertEqual(resp_code, 200)

        kql_dashs = fc.list_kql_dashboards(workspace_id)

        kql_dash_names = [kqld.display_name for kqld in kql_dashs]
        self.assertNotIn(kql_dash3.display_name, kql_dash_names)

