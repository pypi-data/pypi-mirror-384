# Import DeepEvalBaseLLM for proper custom model implementation

from deepeval.models import DeepEvalBaseLLM

from rhesis.sdk.models.base import BaseLLM


class DeepEvalModelWrapper(DeepEvalBaseLLM):
    def __init__(self, model: BaseLLM) -> None:
        self._model = model

    def load_model(self, *args, **kwargs):
        return self._model.load_model(*args, **kwargs)

    def generate(self, prompt: str) -> str:
        return self._model.generate(prompt)

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self, *args, **kwargs) -> str:
        return self._model.get_model_name(*args, **kwargs)
