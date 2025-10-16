# Commented imports below are for classes that don't exist yet or have missing dependencies:
# from wisent_guard.core.activations import Activations  # Module exists but needs Activations class
# from wisent_guard.core.classifier.classifier import ActivationClassifier, Classifier  # classifier.py doesn't exist
# from .steering import SteeringMethod, SteeringType  # steering.py exists but has broken imports (Activations, Classifier)
# from .layer import Layer  # layer.py file doesn't exist in source

from .utils.device import empty_device_cache, preferred_dtype, resolve_default_device, resolve_device, resolve_torch_device
from .models.wisent_model import WisentModel as Model
from .contrastive_pairs.core.set import ContrastivePairSet
from .activations.activations_collector import ActivationCollector

__all__ = [
    "ActivationCollector",
    # "ActivationClassifier",  # Doesn't exist
    # "ActivationHooks",  # Doesn't exist
    # "Activations",  # Doesn't exist
    # "Classifier",  # Doesn't exist
    "ContrastivePairSet",
    # "Layer",  # layer.py doesn't exist in source
    "Model",
    # "ModelParameterOptimizer",  # Doesn't exist
    # "PromptFormat",  # Doesn't exist
    # "SecureCodeEvaluator",  # Doesn't exist
    # "SteeringMethod",  # Exists but has broken imports
    # "SteeringType",  # Exists but has broken imports
    # "TokenScore",  # Doesn't exist
    # "enforce_secure_execution",  # Doesn't exist
    "empty_device_cache",
    "preferred_dtype",
    "resolve_default_device",
    "resolve_device",
    "resolve_torch_device",
]
