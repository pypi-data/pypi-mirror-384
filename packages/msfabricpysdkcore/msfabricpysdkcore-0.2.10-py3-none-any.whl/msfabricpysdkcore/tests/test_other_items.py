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

        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        self.item_name = "testitem" + datetime_str
        self.item_type = "Notebook"
    
    def test_list_other_items(self):

        fc = self.fc

        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'

        list_dashboards = fc.list_dashboards(workspace_id)
        dashboard_names = [dashboard.display_name for dashboard in list_dashboards]
        self.assertGreater(len(list_dashboards), 0)
        self.assertIn("dashboardpbi", dashboard_names)

        # list_datamarts = fc.list_datamarts(workspace_id)
        # datamart_names = [datamart.display_name for datamart in list_datamarts]
        # self.assertGreater(len(list_datamarts), 0)
        # self.assertIn("datamart1", datamart_names)

        list_sql_endpoints = fc.list_sql_endpoints(workspace_id)
        sqlendpoint_names = [sqlendpoint.display_name for sqlendpoint in list_sql_endpoints]
        self.assertGreater(len(list_sql_endpoints), 0)
        self.assertIn("lakelhousewlabels", sqlendpoint_names)

        # list_mirrored_warehouses = fc.list_mirrored_warehouses(self.workspace_id)
        # self.assertGreater(len(list_mirrored_warehouses), 0)

        # list_paginated_reports = fc.list_paginated_reports(self.workspace_id)
        # self.assertGreater(len(list_paginated_reports), 0)