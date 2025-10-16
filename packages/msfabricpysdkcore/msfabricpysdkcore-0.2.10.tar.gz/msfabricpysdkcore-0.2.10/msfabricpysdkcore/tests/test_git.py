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
        
    def test_git(self):

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        ws2_name = "git" + datetime_str
        self.fc.create_workspace(display_name=ws2_name)
        ws2 = self.fc.get_workspace_by_name(name=ws2_name)
        self.fc.assign_to_capacity(workspace_id=ws2.id, capacity_id="9e7e757d-d567-4fb3-bc4f-d230aabf2a00")

        git_provider_details = {'organizationName': 'MngEnvMCAP065039',
                                'projectName': 'fabricdevops',
                                'gitProviderType': 'AzureDevOps',
                                'repositoryName': 'fabricdevops',
                                'branchName': 'main',
                                'directoryName': '/sdkdemoRTI'}

        status_code = self.fc.git_connect(workspace_id=ws2.id, git_provider_details=git_provider_details)

        self.assertEqual(status_code, 200)

        initialization_strategy = "PreferWorkspace"

        status_code = self.fc.git_initialize_connection(workspace_id=ws2.id, initialization_strategy=initialization_strategy)
        self.assertEqual(status_code, 200)

        connection_details = self.fc.git_get_connection(workspace_id=ws2.id)
        self.assertEqual(connection_details['gitConnectionState'], 'ConnectedAndInitialized')

        status = self.fc.git_get_status(workspace_id=ws2.id)
        self.assertTrue(len(status["changes"]) > 0)

        git_credentials = self.fc.get_my_git_credentials('e624ffea-990e-482c-b27c-4ed5adae73c6')
        self.assertTrue(git_credentials["source"] == "Automatic")

        status_code = self.fc.update_from_git(workspace_id=ws2.id, remote_commit_hash=status["remoteCommitHash"])

        self.assertEqual(status_code, 202)

        blubb_lakehouse = False
        for item in ws2.list_items():
            if item.type == "Lakehouse" and item.display_name == "blubb":
                blubb_lakehouse = True

        self.assertTrue(blubb_lakehouse)

        status_code = self.fc.git_disconnect(workspace_id=ws2.id)

        self.assertEqual(status_code, 200)

        ws2.delete()

if __name__ == "__main__":
    unittest.main()
