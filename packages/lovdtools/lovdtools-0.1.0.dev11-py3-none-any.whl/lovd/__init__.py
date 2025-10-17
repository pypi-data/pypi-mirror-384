
"""
LOVD Querying Interfaces
========================

This subpackage provides various interfaces for querying the Leiden Open
Variants Database (LOVD).

"""
from . import cli, client, config, constants

from .client import (
    LOVD_RATE_LIMIT,
    LovdClient,
    get_lovd_variants,
    get_variants_from_config,
    variants_to_dataframe
)
from .config import load_acquisition_config, options
from .constants import (
    ACQUISITION_CONFIG_PATH,
    EMAIL,
    LOVDTOOLS_CACHE_PATH,
    LOVDTOOLS_CONFIG_PATH,
    LOVDTOOLS_DATA_PATH,
    LOVDTOOLS_ROOT_PATH,
    LOVDTOOLS_STATE_PATH,
    LOVDTOOLS_VERSION,
    LOVD_EMAIL,
    NCBI_EMAIL,
    TARGET_GENE_SYMBOLS,
    USER_AGENT_STRING
)


# : package metadata
__author__ = "Caleb R."
__email__ = "hyletic@proton.me"
__version__ = "0.1.0-dev11"


__all__ = [
    # : constants
    "ACQUISITION_CONFIG_PATH",
    "EMAIL",
    "LOVDTOOLS_CACHE_PATH",
    "LOVDTOOLS_CONFIG_PATH",
    "LOVDTOOLS_DATA_PATH",
    "LOVDTOOLS_ROOT_PATH",
    "LOVDTOOLS_STATE_PATH",
    "LOVDTOOLS_VERSION",
    "LOVD_EMAIL",
    "LOVD_RATE_LIMIT",
    "NCBI_EMAIL",
    "TARGET_GENE_SYMBOLS",
    "USER_AGENT_STRING",

    # : modules
    "cli",
    "client",
    "config",
    "constants",

    # : classes
    "LovdClient",

    # : functions
    "get_variants_from_config",
    "get_lovd_variants",
    "load_acquisition_config",
    "variants_to_dataframe",

    # : objects
    "options"
]
