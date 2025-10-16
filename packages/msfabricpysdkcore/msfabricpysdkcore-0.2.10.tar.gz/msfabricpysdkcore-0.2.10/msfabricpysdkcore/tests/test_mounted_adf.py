import unittest
from datetime import datetime
from dotenv import load_dotenv
from time import sleep
from msfabricpysdkcore.coreapi import FabricClientCore

load_dotenv()

# class TestFabricClientCore(unittest.TestCase):

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fc = FabricClientCore()

   
    def test_mounted_adf(self):

        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        definition = {'parts': [{'path': 'mountedDataFactory-content.json',
                                'payload': 'ewogICJkYXRhRmFjdG9yeVJlc291cmNlSWQiOiAiL3N1YnNjcmlwdGlvbnMvYzc3Y2M4ZmMtNDNiYi00ZDQ0LWJkYzUtNmUyMDUxMWVkMmE4L3Jlc291cmNlR3JvdXBzL2ZhYnJpY2RlbW8vcHJvdmlkZXJzL01pY3Jvc29mdC5EYXRhRmFjdG9yeS9mYWN0b3JpZXMvZmFicmljYWRmMjAyNTAzMDYiCn0=',
                                'payloadType': 'InlineBase64'},
                                {'path': '.platform',
                                'payload': 'ewogICIkc2NoZW1hIjogImh0dHBzOi8vZGV2ZWxvcGVyLm1pY3Jvc29mdC5jb20vanNvbi1zY2hlbWFzL2ZhYnJpYy9naXRJbnRlZ3JhdGlvbi9wbGF0Zm9ybVByb3BlcnRpZXMvMi4wLjAvc2NoZW1hLmpzb24iLAogICJtZXRhZGF0YSI6IHsKICAgICJ0eXBlIjogIk1vdW50ZWREYXRhRmFjdG9yeSIsCiAgICAiZGlzcGxheU5hbWUiOiAiZmFicmljYWRmMjAyNTAzMDYiCiAgfSwKICAiY29uZmlnIjogewogICAgInZlcnNpb24iOiAiMi4wIiwKICAgICJsb2dpY2FsSWQiOiAiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIgogIH0KfQ==',
                                'payloadType': 'InlineBase64'}]}

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")

        mounted_adf_name = "mounted_adf" + datetime_str
        mounted_adf = fc.create_mounted_data_factory(workspace_id,
                                                     display_name=mounted_adf_name,
                                                     definition=definition)

        self.assertEqual(mounted_adf.display_name, mounted_adf_name)

        mounted_adfs = fc.list_mounted_data_factories(workspace_id)
        mounted_adf_names = [adf.display_name for adf in mounted_adfs]
        self.assertGreater(len(mounted_adfs), 0)
        self.assertIn(mounted_adf_name, mounted_adf_names)

        adf = fc.get_mounted_data_factory(workspace_id, mounted_data_factory_name=mounted_adf_name)
        self.assertIsNotNone(adf.id)
        self.assertEqual(adf.display_name, mounted_adf_name)

        adf2 = fc.update_mounted_data_factory(workspace_id, adf.id, display_name=f"{mounted_adf_name}2", return_item=True)

        adf = fc.get_mounted_data_factory(workspace_id, mounted_data_factory_id=adf.id)
        self.assertEqual(adf.display_name, f"{mounted_adf_name}2")
        self.assertEqual(adf.id, adf2.id)

        response = fc.update_mounted_data_factory_definition(workspace_id, mounted_data_factory_id=adf.id, definition=adf.definition)
        self.assertIn(response.status_code, [200, 202])

        definition = fc.get_mounted_data_factory_definition(workspace_id, mounted_data_factory_id=adf.id)
        self.assertIn("definition", definition)
        self.assertIn("parts", definition["definition"])
        self.assertGreaterEqual(len(definition["definition"]["parts"]), 2)

        status_code = fc.delete_mounted_data_factory(workspace_id, adf.id)
        self.assertEqual(status_code, 200)
