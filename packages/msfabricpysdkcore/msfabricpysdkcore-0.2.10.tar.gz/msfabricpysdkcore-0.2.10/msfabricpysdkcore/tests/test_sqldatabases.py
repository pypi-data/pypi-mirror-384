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

   
    def test_sql_databases(self):

        fc = self.fc
        workspace_id = '63aa9e13-4912-4abe-9156-8a56e565b7a3'

        # datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")

        # sql_db = fc.create_sql_database(workspace_id, display_name="sqldb" + datetime_str)
        # self.assertEqual(sql_db.display_name, "sqldb" + datetime_str)

        # sql_dbs = fc.list_sql_databases(workspace_id)
        # sql_db_names = [db.display_name for db in sql_dbs]
        # self.assertGreater(len(sql_dbs), 0)
        # self.assertIn("sqldb" + datetime_str, sql_db_names)

        # db = fc.get_sql_database(workspace_id, sql_database_name="sqldb" + datetime_str)
        # self.assertIsNotNone(db.id)
        # self.assertEqual(db.display_name, "sqldb" + datetime_str)

        # db2 = fc.update_sql_database(workspace_id, db.id, display_name=f"sqldb{datetime_str}2", return_item=True)

        # db = fc.get_sql_database(workspace_id, sql_database_id=db.id)
        # self.assertEqual(db.display_name, f"sqldb{datetime_str}2")

        # status_code = fc.delete_sql_database(workspace_id, db.id)
        # self.assertEqual(status_code, 200)
        