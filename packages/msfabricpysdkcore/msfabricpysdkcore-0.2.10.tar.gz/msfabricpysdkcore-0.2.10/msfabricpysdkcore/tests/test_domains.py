import unittest
from dotenv import load_dotenv
from datetime import datetime
from msfabricpysdkcore import FabricClientCore, FabricClientAdmin


load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)

                  
    def test_domains(self):
        fcc = FabricClientCore()
        fca = FabricClientAdmin()

        ws = fcc.get_workspace_by_name("sdkswedencentral")
        cap = fcc.get_capacity(capacity_id=ws.capacity_id)
        principal = {'id': '1dc64c6e-7a10-4ea9-8488-85d0739a377d',  'type': 'User'}

        # Delete if exists
        for dom in fca.list_domains():
            if "sdktestdomain" in dom.display_name:
                dom.delete()

        # Create domain
        domain_name = "sdktestdomains" + datetime.now().strftime("%Y%m%d%H%M%S")
        domain = fca.create_domain(display_name=domain_name)
        self.assertIsNotNone(domain.id)
        self.assertEqual(domain.display_name, domain_name)

        # Get domain by name
        domain_clone = fca.get_domain_by_name(domain_name)
        self.assertIsNotNone(domain_clone.id)
        self.assertEqual(domain_clone.display_name, domain_name)

        # Get domain by id
        domain_clone = fca.get_domain_by_id(domain.id)
        self.assertIsNotNone(domain_clone.id)
        self.assertEqual(domain_clone.display_name, domain_name)

        # List domains
        domains = fca.list_domains()
        self.assertGreater(len(domains), 0)
        domains_ids = [d.id for d in domains]
        self.assertIn(domain.id, domains_ids)

        # Update domain
        domain_new_name = f"{domain_name}2"
        domain_clone = fca.update_domain(domain.id, display_name=domain_new_name, return_item=True)
        self.assertEqual(domain_clone.display_name, domain_new_name)

        # Assign domain workspaces by Ids
        status_code = fca.assign_domain_workspaces_by_ids(domain.id, [ws.id])
        self.assertEqual(status_code, 200)

        # List domain workspaces
        workspaces = fca.list_domain_workspaces(domain.id, workspace_objects=False)
        self.assertGreater(len(workspaces), 0)
        workspaces_ids = [w["id"] for w in workspaces]
        self.assertIn(ws.id, workspaces_ids)

        # Unassign domain workspaces by ids
        status_code = fca.unassign_domain_workspaces_by_ids(domain.id, [ws.id])
        self.assertEqual(status_code, 200)

        workspaces = fca.list_domain_workspaces(domain.id)
        self.assertEqual(len(workspaces), 0)

        # Assign domain workspaces by capacities
        status_code = fca.assign_domain_workspaces_by_capacities(domain.id, [cap.id])
        self.assertEqual(status_code, 202)

        workspaces = fca.list_domain_workspaces(domain.id, workspace_objects=False)
        self.assertGreater(len(workspaces), 0)
        workspaces_ids = [w["id"] for w in workspaces]
        self.assertIn(ws.id, workspaces_ids)

        # Unassign all domain workspaces
        status_code = fca.unassign_all_domain_workspaces(domain.id)
        self.assertEqual(status_code, 200)

        workspaces = fca.list_domain_workspaces(domain.id)
        self.assertEqual(len(workspaces), 0)

        # Assign domain workspaces by principals
        status_code = fca.assign_domains_workspaces_by_principals(domain.id, [principal], wait_for_completion=False)

        self.assertEqual(status_code, 202)

        workspaces = fca.list_domain_workspaces(domain.id, workspace_objects=False)
        self.assertGreater(len(workspaces), 0)
        workspaces_ids = [w["id"] for w in workspaces]
        self.assertIn(ws.id, workspaces_ids)

        # Role assignments bulk assign
        
        principal_2 = {'id': 'e0505016-ef55-4ca7-b106-e085cc201823', 'type': 'User'}
        principals = [principal, principal_2]

        status_code = fca.role_assignments_bulk_assign(domain.id, "Contributors", principals)

        self.assertEqual(status_code, 200)

        # Role assignments bulk unassign
        status_code = fca.role_assignments_bulk_unassign(domain.id, "Contributors", [principal_2])

        self.assertEqual(status_code, 200)

        # Delete domain
        status_code = fca.delete_domain(domain.id)

        self.assertEqual(status_code, 200)

        domains = fca.list_domains()
        domains_ids = [d.id for d in domains]
        self.assertNotIn(domain.id, domains_ids)