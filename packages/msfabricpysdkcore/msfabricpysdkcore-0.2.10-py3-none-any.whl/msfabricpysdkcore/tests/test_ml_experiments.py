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

    
    def test_ml_experiments(self):
            
        fc = self.fc
        workspace_id = '05bc5baa-ef02-4a31-ab20-158a478151d3'
        mlexperiment_name = "mlexp" + datetime.now().strftime("%Y%m%d%H%M%S")
        mlexperiment_name2 = "mlexp2" + datetime.now().strftime("%Y%m%d%H%M%S")

        ml_experiment = fc.create_ml_experiment(workspace_id, display_name=mlexperiment_name)
        self.assertEqual(ml_experiment.display_name, mlexperiment_name)
        
        ml_experiments = fc.list_ml_experiments(workspace_id)
        ml_experiment_names = [mle.display_name for mle in ml_experiments]
        self.assertGreater(len(ml_experiments), 0)
        self.assertIn(mlexperiment_name, ml_experiment_names)

        mle = fc.get_ml_experiment(workspace_id, ml_experiment_name=mlexperiment_name)
        self.assertIsNotNone(mle.id)
        self.assertEqual(mle.display_name, mlexperiment_name)

        mle2 = fc.update_ml_experiment(workspace_id, mle.id, display_name=mlexperiment_name2, return_item=True)

        mle = fc.get_ml_experiment(workspace_id, ml_experiment_id=mle.id)
        self.assertEqual(mle.display_name, mlexperiment_name2)
        self.assertEqual(mle.id, mle2.id)

        status_code = fc.delete_ml_experiment(workspace_id, mle.id)
        self.assertEqual(status_code, 200)