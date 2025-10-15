# bitagere SDK
__version__ = "0.0.8"

# Import main modules for library use
from . import substrate
from . import wallet
from .logging_config import (
    configure_logging,
    DEFAULT_LOG_FORMAT,
    DEFAULT_DATE_FORMAT,
)

# Import main classes for convenience
from .substrate import AgereInterface
from .wallet import Wallet, Keypair

__all__ = [
    "substrate",
    "wallet",
    "AgereInterface",
    "Wallet",
    "Keypair",
    "configure_logging",
    "DEFAULT_LOG_FORMAT",
    "DEFAULT_DATE_FORMAT",
    "__version__",
]
