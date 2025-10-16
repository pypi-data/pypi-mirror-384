from .forecaster import *
from .forecasterModel import *
from .cumulativeBoW import *
import sys

# Import CRAFT models if torch is available
if "torch" in sys.modules:
    from .CRAFTModel import *
    from .CRAFT import *

# Import Transformer models with proper error handling
try:
    from .TransformerDecoderModel import *
except (ImportError, ModuleNotFoundError) as e:
    if "Unsloth GPU requirement not met" in str(e):
        raise ImportError(
            "Error from Unsloth: NotImplementedError: Unsloth currently only works on NVIDIA GPUs and Intel GPUs."
        ) from e
    elif (
        "not currently installed" in str(e)
        or "torch" in str(e)
        or "unsloth" in str(e)
        or "trl" in str(e)
        or "datasets" in str(e)
    ):
        raise ImportError(
            "TransformerDecoderModel requires ML dependencies. Run 'pip install convokit[llm]' to install them."
        ) from e
    else:
        raise

try:
    from .TransformerEncoderModel import *
except (ImportError, ModuleNotFoundError) as e:
    if (
        "not currently installed" in str(e)
        or "torch" in str(e)
        or "transformers" in str(e)
        or "datasets" in str(e)
    ):
        raise ImportError(
            "TransformerEncoderModel requires ML dependencies. Run 'pip install convokit[llm]' to install them."
        ) from e
    else:
        raise

from .TransformerForecasterConfig import *
