# from wisent_guard.core.activations import Activations
# from wisent_guard.core.classifier.classifier import ActivationClassifier, Classifier

from .utils.device import empty_device_cache, preferred_dtype, resolve_default_device, resolve_device, resolve_torch_device
from .models.wisent_model import WisentModel
from .contrastive_pairs.core.set import ContrastivePairSet
from .models.core.atoms import SteeringVector, SteeringPlan

# Simple Layer class for compatibility
class Layer:
    def __init__(self, index: int, type: str = "transformer"):
        self.index = index
        self.type = type

# Compatibility aliases
Model = WisentModel

# from .steering import SteeringMethod, SteeringType

__all__ = [
    # "ActivationClassifier",
    # "ActivationHooks",
    # "Activations",
    # "Classifier",
    "ContrastivePairSet",
    "Layer",
    "Model",
    "WisentModel",
    "SteeringVector",
    "SteeringPlan",
    # "ModelParameterOptimizer",
    # "PromptFormat",
    # "SecureCodeEvaluator",
    # "SteeringMethod",
    # "SteeringType",
    # "TokenScore",
    # "enforce_secure_execution",
    "empty_device_cache",
    "preferred_dtype",
    "resolve_default_device",
    "resolve_device",
    "resolve_torch_device",
]
