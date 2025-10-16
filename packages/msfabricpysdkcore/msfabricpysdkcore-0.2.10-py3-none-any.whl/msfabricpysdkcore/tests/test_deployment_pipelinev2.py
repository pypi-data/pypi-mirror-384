import unittest
from msfabricpysdkcore.coreapi import FabricClientCore
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv()

class TestFabricClientCore(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestFabricClientCore, self).__init__(*args, **kwargs)
        #load_dotenv()
        self.fc = FabricClientCore()
        
    def test_deployment_pipeline2(self):
        fcc = self.fc
        workspace_id = "72d9d955-bd1e-42c7-9746-208f7cbc8956"

        user_id = "e0505016-ef55-4ca7-b106-e085cc201823"
        capacity_id = "9e7e757d-d567-4fb3-bc4f-d230aabf2a00"

        prod_workspace = fcc.create_workspace("sdkswedenproddeploy")
        prod_workspace.assign_to_capacity(capacity_id)

        stages =  [
            {
            "displayName": "Development",
            "description": "Development stage description",
            "isPublic": False
            },
            {
            "displayName": "Production",
            "description": "Production stage description",
            "isPublic":True
            }
        ]

        pipes = fcc.list_deployment_pipelines(with_details=False)
        for pipe in pipes:
            if "sdk" in pipe["displayName"]:
                fcc.delete_deployment_pipeline(deployment_pipeline_id=pipe["id"])
        
        pipe =fcc.create_deployment_pipeline(display_name="sdktestpipeline",
                              description="Test Deployment Pipeline Description",
                              stages=stages)
        
        self.assertIsNotNone(pipe.id)
        pipe_id = pipe.id

        for stage in pipe.stages:
            if stage["displayName"] == "Development":
                dev_stage = stage
            else:
                prod_stage = stage
        
        stage = fcc.get_deployment_pipeline_stage(deployment_pipeline_id=pipe_id,
                                                  stage_id=dev_stage["id"])
        self.assertIsNotNone(stage.id)
        resp = fcc.assign_workspace_to_stage(deployment_pipeline_id=pipe_id,
                              stage_id=dev_stage["id"],
                              workspace_id=workspace_id)
        self.assertEqual(resp, 200)

        resp = fcc.assign_workspace_to_stage(deployment_pipeline_id=pipe_id,
                              stage_id=prod_stage["id"],
                              workspace_id=prod_workspace.id)
        self.assertEqual(resp, 200)
        principal = {
            "id": user_id,
            "type": "User"
        }

        resp = fcc.add_deployment_pipeline_role_assignment(deployment_pipeline_id=pipe_id,principal=principal, role="Admin")
        self.assertEqual(resp, 200)

        roles = fcc.list_deployment_pipeline_role_assignments(deployment_pipeline_id=pipe_id)
        self.assertTrue(len(roles) == 2)

        resp = fcc.delete_deployment_pipeline_role_assignment(deployment_pipeline_id=pipe_id, principal_id=user_id)
        self.assertEqual(resp, 200)

        roles = fcc.list_deployment_pipeline_role_assignments(deployment_pipeline_id=pipe_id)
        self.assertTrue(len(roles) == 1)

        pipes = fcc.list_deployment_pipelines(with_details=False)
        sdk_pipes = [pipe for pipe in pipes  if "sdk" in pipe["displayName"]]
        self.assertTrue(len(sdk_pipes) > 0)

        resp = fcc.deploy_stage_content(deployment_pipeline_id=pipe_id,
                        source_stage_id=dev_stage["id"],
                        target_stage_id=prod_stage["id"], wait_for_completion=False)
        self.assertEqual(resp.status_code, 202)

        ops = fcc.list_deployment_pipeline_operations(deployment_pipeline_id=pipe_id)
        self.assertTrue(len(ops) > 0)

        ops = fcc.get_deployment_pipeline_operation(deployment_pipeline_id=pipe_id, operation_id=ops[0]["id"])
        self.assertIsNotNone(ops["id"])

        stages = fcc.list_deployment_pipeline_stages(deployment_pipeline_id=pipe_id)
        self.assertTrue(len(stages) == 2)

        items = fcc.list_deployment_pipeline_stage_items(deployment_pipeline_id=pipe_id, stage_id=dev_stage["id"])
        self.assertTrue(len(items) == 1)

        updated_pipe = fcc.update_deployment_pipeline(deployment_pipeline_id=pipe.id, display_name="sdknewname", description="newdescription")
        self.assertIsNotNone(updated_pipe.id)

        pipe = fcc.get_deployment_pipeline(pipe_id)
        self.assertIsNotNone(pipe.id)
        self.assertTrue(pipe.display_name == "sdknewname")

        updated_stage = fcc.update_deployment_pipeline_stage(deployment_pipeline_id=pipe_id, stage_id=prod_stage["id"],
                                                     display_name="newname", description="newdescription")
        self.assertIsNotNone(updated_stage["id"])

        stage = fcc.get_deployment_pipeline_stage(deployment_pipeline_id=pipe_id, stage_id=prod_stage["id"])
        self.assertIsNotNone(stage.id)
        self.assertTrue(stage.display_name == "newname")

        for _ in range(10):
            ops = fcc.get_deployment_pipeline_operation(deployment_pipeline_id=pipe_id, operation_id=ops["id"])
            if ops["status"] != "Running":
                break
            else:
                time.sleep(5)

        resp = fcc.unassign_workspace_from_stage(deployment_pipeline_id=pipe_id,stage_id=prod_stage["id"])
        self.assertEqual(resp, 200)

        prod_workspace.delete()

        resp = fcc.delete_deployment_pipeline(deployment_pipeline_id=pipe_id)
        self.assertEqual(resp, 200)