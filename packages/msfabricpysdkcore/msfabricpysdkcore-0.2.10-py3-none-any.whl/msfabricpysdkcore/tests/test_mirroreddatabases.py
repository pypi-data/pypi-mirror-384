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
    
    def test_mirrored_database(self):

        fc = self.fc
        workspace_id = '46425c13-5736-4285-972c-6d034020f3ff'
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")

        mirrored_db_name = "mirrored_db" + datetime_str

        # mirrored_db_w_content = fc.get_mirrored_database(workspace_id, mirrored_database_name="dfsdemo")

        # status = fc.get_mirroring_status(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)
        # self.assertIsNotNone(status)
        # self.assertIn("status", status)

        # status = status["status"]

        # if status == 'Running':
        #     fc.stop_mirroring(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)
        #     sleep(60)
        #     fc.start_mirroring(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)
        # else:
        #     fc.start_mirroring(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)
        #     sleep(60)
        #     fc.stop_mirroring(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)

        # table_status = fc.get_tables_mirroring_status(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)

        # self.assertIsNotNone(table_status)
        # self.assertIn("data", table_status)
        # for _ in range(5):
        #     if len(table_status["data"]) > 0:
        #         break
        #     sleep(60)
        #     table_status = fc.get_tables_mirroring_status(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)
        # self.assertIn("sourceTableName", table_status["data"][0])

        # fc.stop_mirroring(workspace_id=workspace_id, mirrored_database_id=mirrored_db_w_content.id)

        # definition = fc.get_mirrored_database_definition(workspace_id, mirrored_db_w_content.id)
        # self.assertIsNotNone(definition)
        # self.assertIn("definition", definition)
        # self.assertIn("parts", definition["definition"])

        # mirrored_db = fc.create_mirrored_database(workspace_id, display_name=mirrored_db_name)
        
        # mirrored_db_check = fc.get_mirrored_database(workspace_id, mirrored_database_id=mirrored_db.id)
        # self.assertEqual(mirrored_db_check.display_name, mirrored_db_name)
        # self.assertIsNotNone(mirrored_db_check.id)
        # self.assertEqual(mirrored_db_check.id, mirrored_db_check.id)

        # mirrored_dbs = fc.list_mirrored_databases(workspace_id)
        # mirrored_db_names = [md.display_name for md in mirrored_dbs]
        # self.assertGreater(len(mirrored_dbs), 0)
        # self.assertIn(mirrored_db_name, mirrored_db_names)

        # sleep(60)

        # mirrored_db_2 = fc.update_mirrored_database(workspace_id, mirrored_db_check.id,
        #                                             display_name=f"u{mirrored_db_name}", return_item=True)
        # mirrored_db_2 = fc.get_mirrored_database(workspace_id, mirrored_database_id=mirrored_db_2.id)

        # self.assertEqual(mirrored_db_2.display_name, f"u{mirrored_db_name}")

        # status_code = fc.delete_mirrored_database(workspace_id, mirrored_db_2.id)
        # self.assertEqual(status_code, 200)