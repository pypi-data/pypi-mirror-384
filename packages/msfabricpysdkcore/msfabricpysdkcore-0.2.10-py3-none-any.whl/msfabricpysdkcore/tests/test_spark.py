import unittest
from msfabricpysdkcore.coreapi import FabricClientCore
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fc = FabricClientCore()


    def test_spark_workspace_custom_pools(self):
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        pool_name = "pool" + datetime.now().strftime("%Y%m%d%H%M%S")
        # List 

        pools = fc.list_workspace_custom_pools(workspace_id=workspace_id)
        self.assertGreater(len(pools), 0)

        pools = fc.list_workspace_custom_pools(workspace_id=workspace_id)

        self.assertIn("pool1", [p.name for p in pools])
        pool1 = [p for p in pools if p.name == "pool1"][0]

        # Get

        pool1_clone = fc.get_workspace_custom_pool(workspace_id=workspace_id, pool_id=pool1.id)
        self.assertEqual(pool1_clone.id, pool1.id)
        # Create

        pool2 = fc.create_workspace_custom_pool(workspace_id=workspace_id, 
                                        name=pool_name, 
                                        node_family="MemoryOptimized",
                                        node_size="Small", 
                                        auto_scale = {"enabled": True, "minNodeCount": 1, "maxNodeCount": 2},
                                        dynamic_executor_allocation = {"enabled": True, "minExecutors": 1, "maxExecutors": 1})

        self.assertEqual(pool2.name, pool_name)
        self.assertEqual(pool2.node_family, "MemoryOptimized")

        # Update

        pool2 = fc.update_workspace_custom_pool(workspace_id=workspace_id, pool_id=pool2.id,
                                        auto_scale = {"enabled": True, "minNodeCount": 1, "maxNodeCount": 7},
                                        return_item=True)

        self.assertEqual(pool2.auto_scale["maxNodeCount"], 7)
        pool2_clone = fc.get_workspace_custom_pool(workspace_id=workspace_id, pool_id=pool2.id)
        self.assertEqual(pool2_clone.auto_scale["maxNodeCount"], 7)

        # Delete
        status_code = fc.delete_workspace_custom_pool(workspace_id=workspace_id, pool_id=pool2.id)
        self.assertEqual(status_code, 200)

        pools = fc.list_workspace_custom_pools(workspace_id=workspace_id)
        self.assertNotIn(pool_name, [p.name for p in pools])

    def test_workspace_settings(self):
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        # Get

        settings = fc.get_spark_settings(workspace_id)
        self.assertIn("automaticLog", settings)
        
        
        orig_setting = settings["automaticLog"]["enabled"]
        settings["automaticLog"]["enabled"] = not settings["automaticLog"]["enabled"]

        # Update
        settings = fc.update_spark_settings(workspace_id, automatic_log=settings["automaticLog"])
        new_setting = settings["automaticLog"]["enabled"]
        self.assertNotEqual(orig_setting, new_setting)
        self.assertTrue(orig_setting or new_setting)
        self.assertFalse(orig_setting and new_setting)

        settings = fc.get_spark_settings(workspace_id)
        checked_setting = settings["automaticLog"]["enabled"]
        self.assertEqual(checked_setting, new_setting)


if __name__ == "__main__":
    unittest.main()

