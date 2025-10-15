from kserve import Model
from kserve.model_repository import MODEL_MOUNT_DIRS, ModelRepository


class DeeployCustomModelRepository(ModelRepository):
    def __init__(self, model_dir: str = MODEL_MOUNT_DIRS, nthread: int = 1, model: Model = None):
        """Initializes the Deeploy ModelRepository Class
        Parameters:
            model_dir: (str): Path to the local pre trained model file
            nthread (int): Number of processing threads.
            model (DeeployCustomModel):
        """
        super().__init__(model_dir)
        self.nthread = nthread
        self.load_model(model)

    async def load(self, model: str) -> bool:
        """State loading status of model"""
        return self.load_model(model)

    def load_model(self, model: Model) -> bool:
        if model.load():
            self.update(model)
        return model.ready
