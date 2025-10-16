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

    def test_eventstreams(self):

        fcc = self.fc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "94f4b54b-980b-43f9-8b67-ded8028cf1b9"

        eventstreams = fcc.list_eventstreams(workspace_id=workspace_id)
        for eventstream in eventstreams:
            if eventstream.id != item_id:
                resp = fcc.delete_eventstream(workspace_id=workspace_id, eventstream_id=eventstream.id)
                self.assertEqual(resp, 200)

        eventstream_definition = fcc.get_eventstream_definition(workspace_id=workspace_id, eventstream_id=item_id)
        self.assertIn("definition", eventstream_definition)
        definition = eventstream_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"eventstream{date_str}"

        eventstream_new = fcc.create_eventstream(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(eventstream_new.display_name, date_str)

        eventstream_get = fcc.get_eventstream(workspace_id=workspace_id, eventstream_id=eventstream_new.id)
        self.assertEqual(eventstream_get.display_name, date_str)

        eventstreams = fcc.list_eventstreams(workspace_id=workspace_id)
        self.assertEqual(len(eventstreams), 2)

        date_str_updated = date_str + "_updated"
        eventstream_updated = fcc.update_eventstream(workspace_id=workspace_id, eventstream_id=eventstream_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(eventstream_updated.display_name, date_str_updated)

        eventstream_updated = fcc.update_eventstream_definition(workspace_id=workspace_id, eventstream_id=eventstream_new.id, definition=definition)
        self.assertEqual(eventstream_updated.status_code, 200)

        for eventstream in eventstreams:
            if eventstream.id != item_id:
                resp = fcc.delete_eventstream(workspace_id=workspace_id, eventstream_id=eventstream.id)
                self.assertEqual(resp, 200)