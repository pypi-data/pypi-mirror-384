import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_data_pipelines(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "b7746e38-5409-487a-969c-fb7cb026b5d3"

        data_pipelines = fcc.list_data_pipelines(workspace_id=workspace_id)
        for data_pipeline in data_pipelines:
            if data_pipeline.id != item_id:
                resp = fcc.delete_data_pipeline(workspace_id=workspace_id, data_pipeline_id=data_pipeline.id)
                self.assertEqual(resp, 200)

        data_pipeline_definition = fcc.get_data_pipeline_definition(workspace_id=workspace_id, data_pipeline_id=item_id)
        self.assertIn("definition", data_pipeline_definition)
        definition = data_pipeline_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"data_pipeline{date_str}"

        data_pipeline_new = fcc.create_data_pipeline(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(data_pipeline_new.display_name, date_str)

        data_pipeline_get = fcc.get_data_pipeline(workspace_id=workspace_id, data_pipeline_id=data_pipeline_new.id)
        self.assertEqual(data_pipeline_get.display_name, date_str)

        data_pipelines = fcc.list_data_pipelines(workspace_id=workspace_id)
        self.assertEqual(len(data_pipelines), 2)

        date_str_updated = date_str + "_updated"
        data_pipeline_updated = fcc.update_data_pipeline(workspace_id=workspace_id, data_pipeline_id=data_pipeline_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(data_pipeline_updated.display_name, date_str_updated)

        data_pipeline_updated = fcc.update_data_pipeline_definition(workspace_id=workspace_id, data_pipeline_id=data_pipeline_new.id, definition=definition)
        self.assertEqual(data_pipeline_updated.status_code, 200)

        for data_pipeline in data_pipelines:
            if data_pipeline.id != item_id:
                resp = fcc.delete_data_pipeline(workspace_id=workspace_id, data_pipeline_id=data_pipeline.id)
                self.assertEqual(resp, 200)







