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
    
    def test_gateways(self):

        fc = self.fc

        gateways = fc.list_gateways()

        for gw in gateways:
            if "publicKey" not in gw:
                fc.delete_gateway(gw['id'])
            if "publicKey" in gw:
                gw_id = gw['id']

        datetime_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        display_name = 'fabricvnet-' + datetime_str
        gwr =  {'displayName': display_name,
                'capacityId': '9e7e757d-d567-4fb3-bc4f-d230aabf2a00',
                'virtualNetworkAzureResource': {'virtualNetworkName': 'fabricvnet',
                'subnetName': 'default2',
                'resourceGroupName': 'fabricdemo',
                'subscriptionId': 'c77cc8fc-43bb-4d44-bdc5-6e20511ed2a8'},
                'inactivityMinutesBeforeSleep': 30,
                'numberOfMemberGateways': 2,
                'type': 'VirtualNetwork'}

        gw = fc.create_gateway(gwr)
        self.assertEqual(gw['displayName'], gwr['displayName'])

        gateways = fc.list_gateways()
        self.assertEqual(len(gateways), 2)

        gateways = [g for g in gateways if g['displayName'] == display_name]
        gw = gateways[0]

        ras = fc.list_gateway_role_assignments(gw['id'])
        self.assertEqual(len(ras), 1)

        principal = {"id" : "755f273c-98f8-408c-a886-691794938bd8",
                "type" : "ServicePrincipal"}

        new_ras = fc.add_gateway_role_assignment(gw['id'], principal, 'ConnectionCreator')
        self.assertIn("id", new_ras)
        #self.assertEqual(2, len(fc.list_gateway_role_assignments(gw['id'])))

        new_ras = fc.update_gateway_role_assignment(gw['id'], new_ras['id'], 'Admin')
        self.assertEqual('Admin', new_ras['role'])

        new_ras_ = fc.get_gateway_role_assignment(gw['id'], new_ras['id'])
        self.assertEqual('Admin', new_ras_['role'])
        self.assertEqual(new_ras['id'], new_ras_['id'])

        resp_code = fc.delete_gateway_role_assignment(gw['id'], new_ras['id'])
        self.assertEqual(200, resp_code)
        self.assertEqual(1, len(fc.list_gateway_role_assignments(gw['id'])))

        

        gw_members = fc.list_gateway_members(gw_id)
        self.assertGreater(len(gw_members), 0)
        self.assertIn('id', gw_members[0])
        self.assertIn('displayName', gw_members[0])

        display_name_member = "surface_desktop" + datetime_str

        gw_member = fc.update_gateway_member(gateway_id = gw_id, gateway_member_id = gw_id, display_name=display_name_member, enabled=True)
        self.assertEqual(display_name_member, gw_member['displayName'])

        gw_ = fc.get_gateway(gw["id"])
        self.assertEqual(display_name, gw_['displayName'])

        gwr = {
            "type": "OnPremises",
            "displayName": display_name,
            "loadBalancingSetting": "Failover",
            "allowCloudConnectionRefresh": False,
            "allowCustomConnectors": False
            }

        gw_ = fc.update_gateway(gw_id, gwr)
        self.assertEqual(display_name, gw_['displayName'])

        resp_code = fc.delete_gateway(gw["id"])
        self.assertEqual(200, resp_code)

        self.assertEqual(len(fc.list_gateways()), 1)
