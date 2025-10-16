import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientAdmin

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fca = FabricClientAdmin()
                  
    def test_admin_api(self):
        fca = self.fca

        user_id = '1dc64c6e-7a10-4ea9-8488-85d0739a377d'

        # List workspaces
        ws = fca.list_workspaces(name="testitems")[0]

        self.assertEqual(ws.name, "testitems")

        # Get workspace
        ws_clone = fca.get_workspace(workspace_id=ws.id)

        self.assertEqual(ws.id, ws_clone.id)

        # Discover git connections 
      
        git_connections = fca.discover_git_connections()

        self.assertGreater(len(git_connections), 0)

        git_conn = [g for g in git_connections if g['workspaceId'] == '63aa9e13-4912-4abe-9156-8a56e565b7a3'][0]
        self.assertEqual(git_conn['gitProviderDetails']['ownerName'], 'DaSenf1860')

        # List workspace access details

        ws_access = fca.list_workspace_access_details(ws.id)
        principials = ws_access["accessDetails"]
        principials_ids = [p["principal"]["id"] for p in principials]
        self.assertIn(user_id, principials_ids)

        # Get access entities

        access_entities = fca.list_access_entities(user_id, type="Notebook")
        self.assertGreater(len(access_entities), 0)

        # List tenant settings
    
        settings = fca.list_tenant_settings()
        monitoring_setting = [setting for setting in settings if setting['settingName'] == 'PlatformMonitoringTenantSetting'][0]

        self.assertIsNotNone(monitoring_setting)
 
        # List tenant settings capacity overrides
    
        settings_capa = fca.list_capacities_tenant_settings_overrides()
        setting = [s for s in settings_capa if s['id'] == '9E7E757D-D567-4FB3-BC4F-D230AABF2A00']

        self.assertGreater(len(setting), 0)

 
        # List tenant settings overrides on domains

        domain_overrides = fca.list_domain_tenant_settings_overrides()
        len(domain_overrides) == 0 
        self.assertEqual(len(domain_overrides), 0)

        # List tenant settings overrides on workspaces

        workspace_overrides = fca.list_workspace_tenant_settings_overrides()
        wover = [w for w in workspace_overrides if w["id"] == "192333b2-5f89-4da5-ae69-64a3ee4c649c"]
        self.assertIsNotNone(wover)

        # Update tenant settings

        if monitoring_setting["enabled"] == False:
            changed_settings = fca.update_tenant_setting("PlatformMonitoringTenantSetting", enabled=True)
            "tenantSettings" in changed_settings and len(changed_settings["tenantSettings"]) > 0 and changed_settings["tenantSettings"][0]["enabled"] == True
        else: 
            changed_settings = fca.update_tenant_setting("PlatformMonitoringTenantSetting", enabled=False)
            "tenantSettings" in changed_settings and len(changed_settings["tenantSettings"]) > 0 and changed_settings["tenantSettings"][0]["enabled"] == False



        # Update tenant settings capacity overrides

 
        enabledSecurityGroups = [{'graphId': '73ba0244-b701-41ed-96d9-79917b74f5f8', 'name': 'fabricadmins'}]
        excludedSecurityGroups = [{'graphId': '16450670-829a-4b70-b80e-6524eea067cb', 'name': 'fabricuser'}]
        feedback = fca.update_capacity_tenant_setting_override("9e7e757d-d567-4fb3-bc4f-d230aabf2a00",
                                                    "PlatformMonitoringTenantSetting",
                                                    enabled=True,
                                                    excluded_security_groups=excludedSecurityGroups,
                                                    enabled_security_groups=enabledSecurityGroups)
        
        
        # List tenant settings overrides by capacity id
 
        settings_capa = fca.list_capacity_tenant_settings_overrides_by_capacity_id("9e7e757d-d567-4fb3-bc4f-d230aabf2a00")
        setting = [s for s in settings_capa if s['settingName'] == 'PlatformMonitoringTenantSetting']

        self.assertGreater(len(setting), 0)

        # Update tenant settings capacity overrides

        status_code = fca.delete_capacity_tenant_setting_override("9e7e757d-d567-4fb3-bc4f-d230aabf2a00", "PlatformMonitoringTenantSetting")

        self.assertEqual(status_code, 200)

        settings = [set for set in fca.list_capacity_tenant_settings_overrides_by_capacity_id("9e7e757d-d567-4fb3-bc4f-d230aabf2a00") if set["settingName"] == "PlatformMonitoringTenantSetting"]

        self.assertEqual(len(settings), 0)

        self.assertIn("overrides", feedback)
        self.assertGreater(len(feedback["overrides"]), 0)
        self.assertEqual(feedback["overrides"][0]["enabled"], True)

 





        # List items

        item_list = fca.list_items(workspace_id=ws.id)
        self.assertGreater(len(item_list), 0)

        # Get item

        item = fca.get_item(workspace_id=ws.id, item_id=item_list[0].id)
        self.assertEqual(item.id, item_list[0].id)

        # Get item access details

        item_access = fca.list_item_access_details(workspace_id=ws.id, item_id=item_list[0].id)
        principials = item_access["accessDetails"]

        principials_ids = [p["principal"]["id"] for p in principials]

        self.assertIn(user_id, principials_ids)


    def test_labels(self):

        fca = self.fca

        items = [{"id": "e79d7a0e-1741-4ddf-a705-b861f2775f97", "type": "Lakehouse"}]
        label_id = "defa4170-0d19-0005-0007-bc88714345d2"
        resp = fca.bulk_set_labels(items=items, label_id=label_id)
        self.assertEqual(resp["itemsChangeLabelStatus"][0]["status"], "Succeeded")
        resp = fca.bulk_remove_labels(items=items)
        self.assertEqual(resp["itemsChangeLabelStatus"][0]["status"], "Succeeded")

    def test_admin_external_data_shares(self):

        fca = self.fca

        data_shares = fca.list_external_data_shares()
        ws_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"

        data_shares = [d for d in data_shares if d['workspaceId'] == ws_id]

        self.assertGreater(len(data_shares), 0)
        # fca.revoke_external_data_share(external_data_share_id = data_shares[0]['id'], 
        #                                item_id = data_shares[0]['itemId'], 
        #                                workspace_id = data_shares[0]['workspaceId'])
        # data_shares = fca.list_external_data_shares()

        # data_shares = [d for d in data_shares if d['workspaceId'] == ws_id]

        # self.assertEqual(data_shares[0]['status'], 'Revoked')