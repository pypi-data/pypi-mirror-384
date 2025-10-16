import unittest
from dotenv import load_dotenv
from datetime import datetime
from time import sleep
from msfabricpysdkcore import FabricAzureClient

load_dotenv()


class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fac = FabricAzureClient()

    def test_azure_capacity(self):

        fac = self.fac

        subscription_id = "c77cc8fc-43bb-4d44-bdc5-6e20511ed2a8"
        resource_group_name = "fabricdemo"
        capacity_name = "westeuropeajrederer"
        capacity_name_new = "westeuropeajrederer" + datetime.now().strftime("%Y%m%d%H%M%S")

        resp = fac.check_name_availability(subscription_id, "westeurope", capacity_name_new)
        self.assertIn('nameAvailable', resp)
        self.assertEqual(resp['nameAvailable'], True)

        resp = fac.create_or_update_capacity(subscription_id, resource_group_name, capacity_name_new, 
                                            location="westeurope",
                                            properties_administration={"members": ['admin@MngEnvMCAP065039.onmicrosoft.com']},
                                            sku = "F2")
        self.assertIsNotNone(resp.name)
        self.assertEqual(resp.name, capacity_name_new)
        
        resp = fac.get_capacity(subscription_id, resource_group_name, capacity_name_new)
        self.assertIsNotNone(resp.name)
        self.assertEqual(resp.name, capacity_name_new)

        sku = resp.sku['name']

        sleep(60)
        
        resp = fac.delete_capacity(subscription_id, resource_group_name, capacity_name_new)
        self.assertEqual(resp.status_code, 202)


        resp = fac.list_by_resource_group(subscription_id, resource_group_name)
        cap_names = [cap["name"] for cap in resp]
        self.assertIn(capacity_name, cap_names)

        

        resp = fac.list_by_subscription(subscription_id)
        cap_names = [cap["name"] for cap in resp]
        self.assertIn(capacity_name, cap_names)


        resp = fac.list_skus(subscription_id)
        self.assertGreater(len(resp), 0, msg=f"No SKUs found: {resp}")


        resp = fac.list_skus_for_capacity(subscription_id, resource_group_name, capacity_name)
        self.assertGreater(len(resp), 0, msg=f"No SKUs found: {resp}")

        resp = fac.resume_capacity(subscription_id, resource_group_name, capacity_name)
        self.assertEqual(resp.status_code, 202)

        sleep(60)
        resp = fac.suspend_capacity(subscription_id, resource_group_name, capacity_name)
        self.assertEqual(resp.status_code, 202)
        sleep(180)

        if sku != "F4":
            resp = fac.update_capacity(subscription_id, resource_group_name, capacity_name, sku="F4")
            self.assertEqual(resp.sku["name"], "F4")
        else:
            resp = fac.update_capacity(subscription_id, resource_group_name, capacity_name, sku="F2")
            self.assertEqual(resp.sku["name"], "F2")
