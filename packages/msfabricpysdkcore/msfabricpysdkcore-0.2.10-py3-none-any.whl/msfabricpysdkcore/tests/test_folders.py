import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_folders(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        folder_id = "d4f3a9fb-6975-4f5c-9c6b-ca205280966f"
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        display_name = f"sdk_folder_{datetime_str}"

        folder = fcc.create_folder(workspace_id=workspace_id, display_name=display_name, parent_folder_id=folder_id)
        self.assertIsNotNone(folder)
        self.assertEqual(folder.display_name, display_name)

        folder_ = fcc.get_folder(workspace_id=workspace_id, folder_id=folder.id)
        self.assertEqual(folder.id, folder_.id)

        folders = fcc.list_folders(workspace_id=workspace_id)
        folders = [folder for folder in folders if folder.display_name == display_name]
        self.assertGreater(len(folders), 0)

        folder = fcc.update_folder(workspace_id=workspace_id, folder_id=folder.id, display_name=f"sdk_sub_folder_updated_{datetime_str}")
        self.assertEqual(folder.display_name, f"sdk_sub_folder_updated_{datetime_str}")

        folder = fcc.move_folder(workspace_id=workspace_id, folder_id=folder.id)
        self.assertEqual(folder.display_name, f"sdk_sub_folder_updated_{datetime_str}")
        self.assertEqual(folder.parent_folder_id, "")

        folders = fcc.list_folders(workspace_id=workspace_id)

        for f in folders:
            if f.display_name != "sdk_folder":
                f.delete()

        folders = fcc.list_folders(workspace_id=workspace_id)
        self.assertEqual(len(folders), 1)









