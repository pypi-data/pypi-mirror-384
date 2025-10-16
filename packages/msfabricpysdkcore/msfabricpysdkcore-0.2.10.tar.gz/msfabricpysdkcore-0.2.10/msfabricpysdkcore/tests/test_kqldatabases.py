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
    
    def test_kql_database(self):

        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        eventhouse_id = "71994015-66d8-4df2-b57d-46afe7440209"

        creation_payload = {"databaseType" : "ReadWrite",
                            "parentEventhouseItemId" : eventhouse_id}

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        kqldb_name = "kql" + datetime_str
        kqldb = fc.create_kql_database(workspace_id = workspace_id, display_name=kqldb_name,
                                    creation_payload=creation_payload)
        self.assertEqual(kqldb.display_name, kqldb_name)

        kql_databases = fc.list_kql_databases(workspace_id)
        kql_database_names = [kqldb.display_name for kqldb in kql_databases]
        self.assertGreater(len(kql_databases), 0)
        self.assertIn(kqldb_name, kql_database_names)

        kqldb = fc.get_kql_database(workspace_id, kql_database_name=kqldb_name)
        self.assertIsNotNone(kqldb.id)
        self.assertEqual(kqldb.display_name, kqldb_name)
        
        new_name = kqldb_name+"2"
        kqldb2 = fc.update_kql_database(workspace_id, kqldb.id, display_name=new_name, return_item=True)

        kqldb = fc.get_kql_database(workspace_id, kql_database_id=kqldb.id)
        self.assertEqual(kqldb.display_name, new_name)
        self.assertEqual(kqldb.id, kqldb2.id)
        
        response = fc.update_kql_database_definition(workspace_id, kqldb.id, kqldb.definition)
        self.assertIn(response.status_code, [200, 202])

        definition = fc.get_kql_database_definition(workspace_id, kql_database_id=kqldb.id)
        self.assertIn("definition", definition)
        self.assertIn("parts", definition["definition"])
        self.assertGreaterEqual(len(definition["definition"]["parts"]), 3)

        status_code = fc.delete_kql_database(workspace_id, kqldb.id)
        self.assertEqual(status_code, 200)