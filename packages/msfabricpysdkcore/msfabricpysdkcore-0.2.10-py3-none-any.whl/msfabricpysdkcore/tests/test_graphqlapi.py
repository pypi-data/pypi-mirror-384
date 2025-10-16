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

   
    def test_graphql_api(self):

        fc = self.fc
        workspace_id = '46425c13-5736-4285-972c-6d034020f3ff'

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")

        graph_ql = fc.create_graphql_api(workspace_id, display_name="graphql" + datetime_str)
        self.assertEqual(graph_ql.display_name, "graphql" + datetime_str)

        graph_qls = fc.list_graphql_apis(workspace_id)
        graph_ql_names = [gql.display_name for gql in graph_qls]
        self.assertGreater(len(graph_qls), 0)
        self.assertIn("graphql" + datetime_str, graph_ql_names)

        gql = fc.get_graphql_api(workspace_id, graphql_api_name="graphql" + datetime_str)
        self.assertIsNotNone(gql.id)
        self.assertEqual(gql.display_name, "graphql" + datetime_str)

        gql2 = fc.update_graphql_api(workspace_id, gql.id, display_name=f"graphql{datetime_str}2", return_item=True)

        gql = fc.get_graphql_api(workspace_id, graphql_api_id=gql.id)
        self.assertEqual(gql.display_name, f"graphql{datetime_str}2")

        status_code = fc.delete_graphql_api(workspace_id, gql.id)
        self.assertEqual(status_code, 200)
