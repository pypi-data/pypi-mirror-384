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

    def test_connection(self):

        datetime_str = datetime.now().strftime("%Y%m%H%M%S")
        datetime_str
        fc = self.fc

        # display_name = "ContosoCloudConnection" + datetime_str

        # cr = {"connectivityType": "ShareableCloud",
        #     "displayName": display_name,
        #     "connectionDetails": {
        #         'type': "SQL",
        #         'creationMethod': 'SQL',
        #         "parameters": [
        #             {
        #                 "dataType": "Text",
        #                 "name": "server",
        #                 "value": "dfsdemo.database.windows.net"
        #             },
        #             {
        #                 "dataType": "Text",
        #                 "name": "database",
        #                 "value": "dfsdemo"
        #             }
        #             ]},
        #     'privacyLevel': 'Organizational',
        #     'credentialDetails': {'credentials':{'credentialType': 'Basic', 
        #                                         'userName': 'new_user', 
        #                                         'password': 'StrongPassword123!'},
        #                             'singleSignOnType': 'None',
        #                             'connectionEncryption': 'NotEncrypted',
        #                             'skipTestConnection': False}
        # }
            


        # connection = fc.create_connection(connection_request=cr)
        # self.assertIsNotNone(connection)
        # self.assertIn('id', connection)
        # self.assertIn('displayName', connection)
        # self.assertEqual(connection['displayName'], display_name)

        # connection2 = fc.get_connection(connection_name=display_name)
        # self.assertEqual(connection['id'], connection2['id'])


        # connections = fc.list_connections()
        # connection_names = [conn['displayName'] for conn in connections]
        # self.assertIn(display_name, connection_names)

        # id = connection['id']

        # role_assis = fc.list_connection_role_assignments(connection_id=id)
        # self.assertEqual(len(role_assis), 1)

        # principal = {"id" : "755f273c-98f8-408c-a886-691794938bd8",
        #             "type" : "ServicePrincipal"}

        # add_role_assi = fc.add_connection_role_assignment(connection_id=id, principal=principal, role='User')
        # self.assertIsNotNone(add_role_assi)
        # self.assertIn('id', add_role_assi)
        # role_assi_id = add_role_assi['id']

        # role_assis = fc.list_connection_role_assignments(connection_id=id)
        # self.assertEqual(len(role_assis), 2)

        # role_assi = fc.get_connection_role_assignment(connection_id=id,
        #                                               connection_role_assignment_id=role_assi_id)
        # self.assertEqual(role_assi['id'], role_assi_id)

        # role_assi = fc.update_connection_role_assignment(connection_id=id,
        #                                      connection_role_assignment_id=role_assi_id,
        #                                      role='UserWithReshare')
        # self.assertEqual(role_assi['role'], 'UserWithReshare')

        # status_code = fc.delete_connection_role_assignment(connection_id=id,
        #                                                    connection_role_assignment_id=role_assi_id)
        # self.assertEqual(status_code, 200)


        # cr = {
        # "connectivityType": "ShareableCloud",
        # "displayName": f"sqlserver{datetime_str}"
        # }

        # updated_connection = fc.update_connection(connection_id=id, connection_request=cr)
        # self.assertIsNotNone(updated_connection)


        # connection2 = fc.get_connection(connection_id=id)
        # self.assertEqual(connection['id'], connection2['id'])
        # self.assertEqual(connection2['displayName'], f"sqlserver{datetime_str}")

        # status_code = fc.delete_connection(connection_id=id)
        # self.assertEqual(status_code, 200)

