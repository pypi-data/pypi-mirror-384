import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_copy_jobs(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "a9e59ec1-524b-49b1-a185-37e47dc0ceb9"

        copy_jobs = fcc.list_copy_jobs(workspace_id=workspace_id)
        for copy_job in copy_jobs:
            if copy_job.id != item_id:
                resp = fcc.delete_copy_job(workspace_id=workspace_id, copy_job_id=copy_job.id)
                self.assertEqual(resp, 200)

        copy_job_definition = fcc.get_copy_job_definition(workspace_id=workspace_id, copy_job_id=item_id)
        self.assertIn("definition", copy_job_definition)
        definition = copy_job_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"copyjob{date_str}"

        copy_job_new = fcc.create_copy_job(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(copy_job_new.display_name, date_str)

        copy_job_get = fcc.get_copy_job(workspace_id=workspace_id, copy_job_id=copy_job_new.id)
        self.assertEqual(copy_job_get.display_name, date_str)

        copy_jobs = fcc.list_copy_jobs(workspace_id=workspace_id)
        self.assertEqual(len(copy_jobs), 2)

        date_str_updated = date_str + "_updated"
        copy_job_updated = fcc.update_copy_job(workspace_id=workspace_id, copy_job_id=copy_job_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(copy_job_updated.display_name, date_str_updated)

        copy_job_updated = fcc.update_copy_job_definition(workspace_id=workspace_id, copy_job_id=copy_job_new.id, definition=definition)
        self.assertEqual(copy_job_updated.status_code, 200)

        for copy_job in copy_jobs:
            if copy_job.id != item_id:
                resp = fcc.delete_copy_job(workspace_id=workspace_id, copy_job_id=copy_job.id)
                self.assertEqual(resp, 200)







