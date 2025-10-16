
# import unittest
# from dotenv import load_dotenv
# from msfabricpysdkcore import FabricClientCore
# from datetime import datetime
# from time import sleep
# load_dotenv()

# class TestFabricClientCore(unittest.TestCase):

#     def __init__(self, *args, **kwargs):
#         super(TestFabricClientCore, self).__init__(*args, **kwargs)
                  
#     def test_eventstream_topology(self):

        # fcc = FabricClientCore()

        # workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"

        # item_id = "94f4b54b-980b-43f9-8b67-ded8028cf1b9"
        # custom_destination_id = "acd90d61-2792-4494-9f17-c822f2fb984d"
        # custom_source_id = "9f382928-7d42-43f9-b02b-1b1352ad3ecd"
        # source_id = "e58db369-e473-40f4-bedd-022b60540b17"
        # destination_id = "2446e6cf-98c9-45cb-a102-78d2ca3eb257"


        # topology = fcc.get_eventstream_topology(workspace_id, item_id)
        # self.assertIsNotNone(topology)
        # self.assertIn("sources", topology)
        # self.assertIn("destinations", topology)

        # destination = fcc.get_eventstream_destination(workspace_id, item_id, destination_id)
        # self.assertIsNotNone(destination)
        # self.assertEqual(destination["id"], destination_id)

        # destination_conn = fcc.get_eventstream_destination_connection(workspace_id, item_id, custom_destination_id)
        # self.assertIsNotNone(destination_conn)
        # self.assertIn("fullyQualifiedNamespace", destination_conn)

        # source = fcc.get_eventstream_source(workspace_id, item_id, source_id)
        # self.assertIsNotNone(source)
        # self.assertEqual(source["id"], source_id)

        # source_conn = fcc.get_eventstream_source_connection(workspace_id, item_id, custom_source_id)
        # self.assertIsNotNone(source_conn)
        # self.assertIn("fullyQualifiedNamespace", source_conn)

        # resp = fcc.pause_eventstream(workspace_id, item_id)
        # self.assertEqual(resp, 200)

        # def resume():
        #     resp = fcc.resume_eventstream(workspace_id, item_id, start_type="Now")
        #     self.assertEqual(resp, 200)

        # for _ in range(12):
        #     try:
        #         resume()
        #         break
        #     except Exception as e:
        #         sleep(5)
        
        # resp = fcc.pause_eventstream_source(workspace_id, item_id, source_id)
        # self.assertEqual(resp, 200)

        # resp = fcc.pause_eventstream_destination(workspace_id, item_id, destination_id)
        # self.assertEqual(resp, 200)

        # resp = fcc.resume_eventstream_source(workspace_id, item_id, source_id, start_type="Now")
        # self.assertEqual(resp, 200)

        # def resume():
        #     resp = fcc.resume_eventstream_destination(workspace_id, item_id, destination_id, start_type="Now")
        #     self.assertEqual(resp, 200)
        
        # for _ in range(12):
        #     try:
        #         resume()
        #         break
        #     except Exception as e:
        #         sleep(5)


