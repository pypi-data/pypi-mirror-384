import unittest
from dotenv import load_dotenv
from datetime import datetime
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fc = FabricClientCore()
        
    
    def test_end_to_end_workspace(self):
        fc = self.fc
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        display_name = "testws" + datetime_str

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        workspace_name_new = "newws" + datetime_str
        ws_created = fc.create_workspace(display_name=display_name,
                                              description="test workspace", 
                                              exists_ok=False)
        # Add assertions here to verify the result
        self.assertEqual(ws_created.display_name, display_name)
        workspace_id = ws_created.id
        ws = fc.get_workspace_by_id(id = workspace_id)
        self.assertEqual(ws.display_name, display_name)
        self.assertEqual(ws.description, "test workspace")

#   def test_assign_to_capacity(self):
        
        result_status_code = fc.assign_to_capacity(workspace_id=ws.id, 
                                                        capacity_id="9e7e757d-d567-4fb3-bc4f-d230aabf2a00")
        self.assertEqual(result_status_code, 202)
      

#    def test_list_workspaces(self):
        
        result = fc.list_workspaces()
        display_names = [ws.display_name for ws in result]
        self.assertIn(display_name, display_names)

        for ws in result:
            if ws.display_name == display_name:
                self.assertEqual(ws.capacity_id, "9e7e757d-d567-4fb3-bc4f-d230aabf2a00")


  #  def test_get_workspace_by_name(self):

        workspace_name = display_name
        ws = fc.get_workspace_by_name(name = workspace_name)
        self.assertEqual(ws.display_name, display_name)

 #   def test_get_workspace_by_id(self):
        ws = fc.get_workspace_by_id(id = workspace_id)
        self.assertEqual(display_name, ws.display_name)


#    def test_get_workspace(self):
        result = fc.get_workspace_by_id(id = workspace_id)
        self.assertEqual(result.display_name, display_name)
    
 #   def test_add_role_assignment(self):
        result_status = fc.add_workspace_role_assignment(workspace_id = ws.id,
                                                         principal = {"id" : "755f273c-98f8-408c-a886-691794938bd8",
                                                                        "type" : "ServicePrincipal"},
                                                         role = 'Member')
        
        self.assertEqual(result_status, 201)

 #   def test_get_workspace_role_assignments(self):
        result = fc.list_workspace_role_assignments(workspace_id = ws.id)
        self.assertTrue(len(result) == 2)
        for user in result:
            if user["principal"]["displayName"] == "fabrictestuser":
                self.assertEqual(user["role"], "Member")

        # Get get_workspace_role_assignment

        result = fc.get_workspace_role_assignment(workspace_id = ws.id, 
                                                  workspace_role_assignment_id = user["id"])
        
        self.assertEqual(result["role"], "Member")

#    def test_update_workspace_role_assignment(self):

        result_status_code = fc.update_workspace_role_assignment(workspace_id = ws.id, 
                                                                      role = "Contributor", 
                                                                      workspace_role_assignment_id=  user["id"])
        
        self.assertEqual(result_status_code, 200)

        result = fc.list_workspace_role_assignments(workspace_id = ws.id)
        self.assertTrue(len(result) == 2)
        for user in result:
            if user["principal"]["displayName"] == "fabrictestuser":
                self.assertTrue(user["role"] == "Contributor")

#   def test_delete_role_assignment(self):
        result_status_code = fc.delete_workspace_role_assignment(workspace_id = ws.id,
                                                                 workspace_role_assignment_id = user["id"])
        self.assertEqual(result_status_code, 200)

 #   def test_get_workspace_role_assignments(self):
        result = fc.list_workspace_role_assignments(workspace_id = ws.id)
        self.assertTrue(len(result) == 1)
        user = result[0]
#        self.assertTrue(user["principal"]["displayName"] == "fabricapi")
        self.assertTrue(user["role"] == "Admin")

#    def test_update_workspace(self):
        ws_updated = fc.update_workspace(workspace_id=ws.id, 
                                              display_name=workspace_name_new, 
                                              description="new description")
        self.assertEqual(ws_updated.display_name, workspace_name_new)
        self.assertEqual(ws_updated.description, "new description")
        ws = fc.get_workspace_by_id(id = ws.id)
        self.assertEqual(ws.display_name, workspace_name_new)
        self.assertEqual(ws.description, "new description")

#    def test_unassign_from_capacity(self):

        result_status_code = fc.unassign_from_capacity(workspace_id=ws.id)
        self.assertEqual(result_status_code, 202)
        ws = fc.get_workspace_by_id(ws.id)
        self.assertEqual(ws.capacity_id, None)

        # result = fc.provision_identity(workspace_id=ws.id)
        # self.assertIsNotNone(result["applicationId"])
        # fc.deprovision_identity(workspace_id=ws.id)



#    def test_delete_workspace(self):
        result_status = fc.delete_workspace(display_name=workspace_name_new)
        self.assertEqual(result_status, 200)

    def test_list_capacities(self):
        result = self.fc.list_capacities()
        self.assertTrue(len(result) > 0)
        cap_ids = [cap.id for cap in result]
        self.assertIn("9e7e757d-d567-4fb3-bc4f-d230aabf2a00", cap_ids)

    def test_get_capacity(self):
        capacity = self.fc.get_capacity(capacity_id = "9e7e757d-d567-4fb3-bc4f-d230aabf2a00")
        self.assertEqual(capacity.id, "9e7e757d-d567-4fb3-bc4f-d230aabf2a00")

        cap = self.fc.get_capacity(capacity_name= capacity.display_name)

        self.assertEqual(capacity.id, cap.id)
        self.assertIsNotNone(cap.state)
        self.assertIsNotNone(cap.sku)
        self.assertIsNotNone(cap.region)

    def test_network_communication_policy(self):
        fcc = self.fc
        workspace_id = "5902cade-5261-4afa-96f4-266167ac81a1"
        policy = fcc.get_network_communication_policy(workspace_id=workspace_id)
        self.assertIn('inbound', policy)
        self.assertIn('outbound', policy)
        
        inbound = {'publicAccessRules': {'defaultAction': 'Allow'}}
        outbound = {'publicAccessRules': {'defaultAction': 'Allow'}}

        resp = fcc.set_network_communication_policy(workspace_id=workspace_id, inbound=inbound, outbound=outbound)
        self.assertEqual(resp.status_code, 200)

if __name__ == "__main__":
    unittest.main()