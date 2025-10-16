import unittest
from datetime import datetime
from dotenv import load_dotenv
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fc = FabricClientCore()
        
    def test_spark_job_definitions(self):
        
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        spark_job_definition_name = f"sjd{datetime_str}"

        spark_job_definition_w_content = fc.get_spark_job_definition(workspace_id, spark_job_definition_name="helloworld")

        result = fc.run_on_demand_spark_job_definition(workspace_id=workspace_id, 
                                                        spark_job_definition_id=spark_job_definition_w_content.id,
                                                        job_type="sparkjob")
        self.assertIsNotNone(result)
        self.assertEqual(result.job_type, "sparkjob")
        definition = fc.get_spark_job_definition_definition(workspace_id, spark_job_definition_w_content.id)
        
        self.assertIsNotNone(definition)
        self.assertIn("definition", definition)
        definition = definition["definition"]

        spark_job_definition = fc.create_spark_job_definition(workspace_id, display_name=spark_job_definition_name)
        fc.update_spark_job_definition_definition(workspace_id, spark_job_definition.id, definition=definition)
        spark_job_definition = fc.get_spark_job_definition(workspace_id, spark_job_definition_id=spark_job_definition.id)
        self.assertEqual(spark_job_definition.display_name, spark_job_definition_name)
        self.assertIsNotNone(spark_job_definition.definition)

        spark_job_definitions = fc.list_spark_job_definitions(workspace_id)
        spark_job_definition_names = [sjd.display_name for sjd in spark_job_definitions]
        self.assertGreater(len(spark_job_definitions), 0)
        self.assertIn(spark_job_definition_name, spark_job_definition_names)

        sjd = fc.get_spark_job_definition(workspace_id, spark_job_definition_name=spark_job_definition_name)
        self.assertIsNotNone(sjd.id)
        self.assertEqual(sjd.display_name, spark_job_definition_name)

        sjd = fc.update_spark_job_definition(workspace_id, sjd.id, display_name=f"{spark_job_definition_name}2", return_item=True)
        sjd = fc.get_spark_job_definition(workspace_id, spark_job_definition_id=sjd.id)
        self.assertEqual(sjd.display_name, f"{spark_job_definition_name}2")

        status_code = fc.delete_spark_job_definition(workspace_id, sjd.id)
        self.assertEqual(status_code, 200)
