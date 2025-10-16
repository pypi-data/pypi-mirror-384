import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_apache_airflow_job(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "4e685286-d909-4ccb-911f-590ee3c3df14"

        apache_airflow_job = fcc.list_apache_airflow_jobs(workspace_id=workspace_id)
        for apache_airflow_job in apache_airflow_job:
            if apache_airflow_job.id != item_id:
                resp = fcc.delete_apache_airflow_job(workspace_id=workspace_id, apache_airflow_job_id=apache_airflow_job.id)
                self.assertEqual(resp, 200)

        apache_airflow_job_definition = fcc.get_apache_airflow_job_definition(workspace_id=workspace_id, apache_airflow_job_id=item_id)
        self.assertIn("definition", apache_airflow_job_definition)
        definition = apache_airflow_job_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"copyjob{date_str}"

        apache_airflow_job_new = fcc.create_apache_airflow_job(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(apache_airflow_job_new.display_name, date_str)

        apache_airflow_job_get = fcc.get_apache_airflow_job(workspace_id=workspace_id, apache_airflow_job_id=apache_airflow_job_new.id)
        self.assertEqual(apache_airflow_job_get.display_name, date_str)

        apache_airflow_job = fcc.list_apache_airflow_jobs(workspace_id=workspace_id)
        self.assertEqual(len(apache_airflow_job), 2)

        date_str_updated = date_str + "_updated"
        apache_airflow_job_updated = fcc.update_apache_airflow_job(workspace_id=workspace_id, apache_airflow_job_id=apache_airflow_job_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(apache_airflow_job_updated.display_name, date_str_updated)

        apache_airflow_job_updated = fcc.update_apache_airflow_job_definition(workspace_id=workspace_id, apache_airflow_job_id=apache_airflow_job_new.id, definition=definition)
        self.assertEqual(apache_airflow_job_updated.status_code, 200)

        for apache_airflow_job in apache_airflow_job:
            if apache_airflow_job.id != item_id:
                resp = fcc.delete_apache_airflow_job(workspace_id=workspace_id, apache_airflow_job_id=apache_airflow_job.id)
                self.assertEqual(resp, 200)







