import unittest
from msfabricpysdkcore.coreapi import FabricClientCore
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fc = FabricClientCore()
        self.workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        self.item_id = "9a2edf0f-2318-4179-80d0-1002f3dae7b1"


    def test_jobs_end_to_end(self):
        job = self.fc.run_on_demand_item_job(workspace_id=self.workspace_id,
                                            item_id=self.item_id,
                                            job_type="RunNotebook")
        
        self.assertEqual(job.item_id, self.item_id)
        self.assertEqual(job.workspace_id, self.workspace_id)
        self.assertEqual(job.job_type, "RunNotebook")
        self.assertIn(job.status, ["NotStarted", "InProgress", "Failed"])
        self.assertEqual(job.invoke_type, "Manual")

        job2 = self.fc.get_item_job_instance(workspace_id=self.workspace_id,
                                        item_id=self.item_id,
                                        job_instance_id=job.id)
        
        self.assertEqual(job.id, job2.id)

        status_code = self.fc.cancel_item_job_instance(workspace_id=self.workspace_id,
                                                  item_id=self.item_id,
                                                  job_instance_id=job.id)

        self.assertEqual(status_code, 202)

        job_instances = self.fc.list_item_job_instances(workspace_id=self.workspace_id,
                                                        item_id=self.item_id)
        
        self.assertGreaterEqual(len(job_instances), 1)

    def test_item_schedules(self):

        fc = self.fc


        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        spark_job_definition_name = f"sjd{datetime_str}"

        spark_job_definition_w_content = fc.get_spark_job_definition(workspace_id, spark_job_definition_name="helloworld")
        definition = fc.get_spark_job_definition_definition(workspace_id, spark_job_definition_w_content.id)


        self.assertIsNotNone(definition)
        self.assertIn("definition", definition)
        definition = definition["definition"]

        spark_job_definition = fc.create_spark_job_definition(workspace_id, display_name=spark_job_definition_name, definition=definition)

        self.assertIsNotNone(spark_job_definition)

        configuration = {'type': 'Daily',
                         'startDateTime': '2024-11-21T00:00:00',
                         'endDateTime': '2028-11-08T23:59:00',
                         'localTimeZoneId': 'Romance Standard Time',
                         'times': ['15:39']}

        schedule = spark_job_definition.create_item_schedule(job_type="sparkjob", configuration=configuration, enabled=True)

        schedule_id = schedule["id"]
        schedule_check = spark_job_definition.get_item_schedule(schedule_id=schedule_id, job_type="sparkjob")
        self.assertIsNotNone(schedule_check)
        self.assertEqual(schedule_check["id"], schedule_id)

        schedule_new = spark_job_definition.update_item_schedule(schedule_id=schedule_id, job_type="sparkjob", configuration=configuration, enabled=False)
        self.assertIsNotNone(schedule_new)

        item_id = spark_job_definition.id

        schedule_check = spark_job_definition.get_item_schedule(schedule_id=schedule_id, job_type="sparkjob")
        self.assertEqual(schedule_check["id"], schedule_id)
        self.assertFalse(schedule_check["enabled"])
        list_schedules = fc.list_item_schedules(workspace_id, item_id, job_type="sparkjob")

        self.assertGreater(len(list_schedules), 0)

        spark_job_definition.delete()

if __name__ == "__main__":
    unittest.main()

