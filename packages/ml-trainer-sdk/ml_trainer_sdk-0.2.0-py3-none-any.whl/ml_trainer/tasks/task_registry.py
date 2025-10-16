# decorator design pattern
from .timeseries import TimeSeriesFactory
from .image_classification import ImageClassificationFactory
from .llm_finetuning import LLMTaskFactory

task_factory_registry = {
    "timeseries": TimeSeriesFactory(),
    "image_classification": ImageClassificationFactory(),
    "llm_finetuning": LLMTaskFactory(),
}

def register_task(name):
    def wrapper(cls):
        task_factory_registry[name] = cls()
        return cls
    return wrapper