# ============================================
# dsf_aml_sdk/__init__.py
# ============================================
"""DSF AML SDK - Adaptive Machine Learning with Knowledge Distillation"""

__version__ = '1.0.69'
__author__ = 'api-dsfuptech'
__email__ = 'contacto@softwarefinanzas.com.co'

from .client import AMLSDK
from .exceptions import AMLSDKError, ValidationError, LicenseError, APIError, RateLimitError
from .models import Field, Config, EvaluationResult, DistillationResult

__all__ = [
    'AMLSDK',
    'Field',
    'Config',
    'EvaluationResult',
    'DistillationResult',
    'AMLSDKError',
    'ValidationError',
    'LicenseError',
    'APIError',
    'RateLimitError'
]