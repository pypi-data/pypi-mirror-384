import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_anomaly_detectors(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "9d47b06e-d7c3-40a3-8e6d-6263fb1779a2"

        anomaly_detectors = fcc.list_anomaly_detectors(workspace_id=workspace_id)
        for anomaly_detector in anomaly_detectors:
            if anomaly_detector.id != item_id:
                resp = fcc.delete_anomaly_detector(workspace_id=workspace_id, anomaly_detector_id=anomaly_detector.id)
                self.assertEqual(resp, 200)

        anomaly_detector_definition = fcc.get_anomaly_detector_definition(workspace_id=workspace_id, anomaly_detector_id=item_id)
        self.assertIn("definition", anomaly_detector_definition)
        definition = anomaly_detector_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"anomalydetector{date_str}"

        anomaly_detector_new = fcc.create_anomaly_detector(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(anomaly_detector_new.display_name, date_str)

        anomaly_detector_get = fcc.get_anomaly_detector(workspace_id=workspace_id, anomaly_detector_id=anomaly_detector_new.id)
        self.assertEqual(anomaly_detector_get.display_name, date_str)

        anomaly_detectors = fcc.list_anomaly_detectors(workspace_id=workspace_id)
        self.assertEqual(len(anomaly_detectors), 2)

        date_str_updated = date_str + "_updated"
        anomaly_detector_updated = fcc.update_anomaly_detector(workspace_id=workspace_id, anomaly_detector_id=anomaly_detector_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(anomaly_detector_updated.display_name, date_str_updated)

        anomaly_detector_updated = fcc.update_anomaly_detector_definition(workspace_id=workspace_id, anomaly_detector_id=anomaly_detector_new.id, definition=definition)
        self.assertEqual(anomaly_detector_updated.status_code, 200)

        for anomaly_detector in anomaly_detectors:
            if anomaly_detector.id != item_id:
                resp = fcc.delete_anomaly_detector(workspace_id=workspace_id, anomaly_detector_id=anomaly_detector.id)
                self.assertEqual(resp, 200)







