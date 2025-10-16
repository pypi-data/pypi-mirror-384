import unittest
from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fc = FabricClientCore()

    def test_environments_crudl(self):
        fcc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        item_id = '35a08bcb-ff8c-40f7-93ea-b86dc1affce5'

        environments = fcc.list_environments(workspace_id=workspace_id)
        for environment in environments:
            if environment.id != item_id:
                resp = fcc.delete_environment(workspace_id=workspace_id, environment_id=environment.id)
                self.assertEqual(resp, 200)


        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"environment{date_str}"

        environment_new = fcc.create_environment(workspace_id=workspace_id, display_name=date_str)

        self.assertEqual(environment_new.display_name, date_str)

        environment_get = fcc.get_environment(workspace_id=workspace_id, environment_id=environment_new.id)
        self.assertEqual(environment_get.display_name, date_str)

        environments = fcc.list_environments(workspace_id=workspace_id)
        self.assertEqual(len(environments), 2)

        date_str_updated = date_str + "_updated"
        environment_updated = fcc.update_environment(workspace_id=workspace_id, environment_id=environment_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(environment_updated.display_name, date_str_updated)

        for environment in environments:
            if environment.id != item_id:
                resp = fcc.delete_environment(workspace_id=workspace_id, environment_id=environment.id)
                self.assertEqual(resp, 200)

    def test_environment_details(self):
        fc = FabricClientCore()
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        environment_id = '35a08bcb-ff8c-40f7-93ea-b86dc1affce5'

        published_settings = fc.get_published_settings(workspace_id=workspace_id, environment_id=environment_id)
        self.assertIsNotNone(published_settings)
        self.assertIn("instancePool", published_settings)
        self.assertIn("dynamicExecutorAllocation", published_settings)
        staging_settings = fc.get_staging_settings(workspace_id=workspace_id, environment_id=environment_id)
        self.assertIsNotNone(staging_settings)
        self.assertIn("instancePool", staging_settings)
        self.assertIn("dynamicExecutorAllocation", staging_settings)
        if staging_settings["driverCores"] == 8:
            driver_cores = 4
        else:
            driver_cores = 8
        updated_settings = fc.update_staging_settings(workspace_id=workspace_id, environment_id=environment_id, driver_cores=driver_cores)
        self.assertIn("instancePool", updated_settings)
        self.assertIn("dynamicExecutorAllocation", updated_settings)
        self.assertEqual(updated_settings["driverCores"], driver_cores)
        updated_settings = fc.get_staging_settings(workspace_id=workspace_id, environment_id=environment_id)
        self.assertIn("instancePool", updated_settings)
        self.assertIn("dynamicExecutorAllocation", updated_settings)
        self.assertEqual(updated_settings["driverCores"], driver_cores)


    def test_environment_spark_libraries(self):
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        environment_id = '35a08bcb-ff8c-40f7-93ea-b86dc1affce5'

        resp = fc.get_published_libraries(workspace_id, environment_id)
        self.assertIn('customLibraries', resp)
        self.assertIn('wheelFiles', resp['customLibraries'])
        self.assertIn('msfabricpysdkcore-0.2.6-py3-none-any.whl', resp['customLibraries']['wheelFiles'])

        resp = fc.upload_staging_library(workspace_id, environment_id, 'dummy.whl')
        self.assertEqual(resp.status_code, 200)
        
        resp = fc.get_staging_libraries(workspace_id, environment_id)

        self.assertIn('customLibraries', resp)
        self.assertIn('wheelFiles', resp['customLibraries'])
        self.assertIn('dummy.whl', resp['customLibraries']['wheelFiles'])

        
        resp = fc.publish_environment(workspace_id, environment_id)
        self.assertIn('publishDetails', resp)
        self.assertIn('state', resp['publishDetails'])
        self.assertEqual(resp['publishDetails']['state'].lower(), 'running')

        
        resp = fc.cancel_publish(workspace_id, environment_id)
        self.assertIn('publishDetails', resp)
        self.assertIn('state', resp['publishDetails'])
        self.assertEqual(resp['publishDetails']['state'].lower(), 'cancelled')

        resp = fc.delete_staging_library(workspace_id, environment_id, 'dummy.whl')
        self.assertEqual(resp.status_code, 200)

        resp = fc.get_staging_libraries(workspace_id, environment_id)

        self.assertIn('customLibraries', resp)
        self.assertIn('wheelFiles', resp['customLibraries'])
        self.assertNotIn('dummy.whl', resp['customLibraries']['wheelFiles'])


        



