import unittest
from dotenv import load_dotenv
from msfabricpysdkcore import FabricClientCore
from datetime import datetime
load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        self.fcc = FabricClientCore()
                  
    def test_mirrored_azure_databricks_catalog(self):
        fcc = self.fcc

        workspace_id = "05bc5baa-ef02-4a31-ab20-158a478151d3"
        item_id = "eb5a54af-f282-4612-97c1-95120620b5d3"
        connection_id = "f7ac4f29-a70e-4868-87a1-9cdd92eacfa0"

        catalog_name = "unitycatalogdbxsweden"
        schema_name = "testinternal"
        table_name = "internal_customer"

        mirrored_azure_databricks_catalog = fcc.list_mirrored_azure_databricks_catalogs(workspace_id=workspace_id)
        for mirrored_azure_databricks_catalog in mirrored_azure_databricks_catalog:
            if mirrored_azure_databricks_catalog.id != item_id:
                resp = fcc.delete_mirrored_azure_databricks_catalog(workspace_id=workspace_id, mirrored_azure_databricks_catalog_id=mirrored_azure_databricks_catalog.id)
                self.assertEqual(resp, 200)

        mirrored_azure_databricks_catalog_definition = fcc.get_mirrored_azure_databricks_catalog_definition(workspace_id=workspace_id, mirrored_azure_databricks_catalog_id=item_id)
        self.assertIn("definition", mirrored_azure_databricks_catalog_definition)
        definition = mirrored_azure_databricks_catalog_definition["definition"]

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = date_str.replace(" ", "T").replace(":", "").replace("-", "")
        date_str = f"copyjob{date_str}"

        mirrored_azure_databricks_catalog_new = fcc.create_mirrored_azure_databricks_catalog(workspace_id=workspace_id, display_name=date_str, definition=definition)

        self.assertEqual(mirrored_azure_databricks_catalog_new.display_name, date_str)

        mirrored_azure_databricks_catalog_get = fcc.get_mirrored_azure_databricks_catalog(workspace_id=workspace_id, mirrored_azure_databricks_catalog_id=mirrored_azure_databricks_catalog_new.id)
        self.assertEqual(mirrored_azure_databricks_catalog_get.display_name, date_str)

        mirrored_azure_databricks_catalog = fcc.list_mirrored_azure_databricks_catalogs(workspace_id=workspace_id)
        self.assertEqual(len(mirrored_azure_databricks_catalog), 2)

        date_str_updated = date_str + "_updated"
        mirrored_azure_databricks_catalog_updated = fcc.update_mirrored_azure_databricks_catalog(workspace_id=workspace_id, mirrored_azure_databricks_catalog_id=mirrored_azure_databricks_catalog_new.id, display_name=date_str_updated, return_item=True)
        self.assertEqual(mirrored_azure_databricks_catalog_updated.display_name, date_str_updated)

        mirrored_azure_databricks_catalog_updated = fcc.update_mirrored_azure_databricks_catalog_definition(workspace_id=workspace_id, mirrored_azure_databricks_catalog_id=mirrored_azure_databricks_catalog_new.id, definition=definition)
        self.assertEqual(mirrored_azure_databricks_catalog_updated.status_code, 200)

        for mirrored_azure_databricks_catalog in mirrored_azure_databricks_catalog:
            if mirrored_azure_databricks_catalog.id != item_id:
                resp = fcc.delete_mirrored_azure_databricks_catalog(workspace_id=workspace_id, mirrored_azure_databricks_catalog_id=mirrored_azure_databricks_catalog.id)
                self.assertEqual(resp, 200)

        catalogs = fcc.discover_mirrored_azure_databricks_catalogs(workspace_id=workspace_id, databricks_workspace_connection_id=connection_id)
        self.assertEqual(len([cat["name"] for cat in catalogs if cat["name"] == catalog_name]), 1)

        schemas = fcc.discover_mirrored_azure_databricks_catalog_schemas(workspace_id=workspace_id, catalog_name=catalog_name, databricks_workspace_connection_id=connection_id)
        self.assertEqual(len([cat["name"] for cat in schemas if cat["name"] == schema_name]), 1)

        tables = fcc.discover_mirrored_azure_databricks_catalog_tables(workspace_id=workspace_id, catalog_name=catalog_name, schema_name=schema_name, databricks_workspace_connection_id=connection_id)
        self.assertEqual(len([cat["name"] for cat in tables if cat["name"] == table_name]), 1)

        status = fcc.refresh_mirrored_azure_databricks_catalog_metadata(workspace_id=workspace_id,
                                                               item_id= item_id, wait_for_completion=False)
        self.assertEqual(status, 202)
        









