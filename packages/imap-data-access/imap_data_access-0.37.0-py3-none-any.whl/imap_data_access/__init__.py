"""Data Access for the IMAP Mission.

The Interstellar Mapping and Acceleration Probe (IMAP) is a NASA mission to study the
heliosphere. This package contains the data access tools for the IMAP mission. It
provides a convenient way to query the IMAP data archive and download data files.
"""

import importlib.metadata
import os
from pathlib import Path

from imap_data_access.file_validation import (
    AncillaryFilePath,
    CadenceFilePath,
    DependencyFilePath,
    ImapFilePath,
    QuicklookFilePath,
    ScienceFilePath,
    SPICEFilePath,
)
from imap_data_access.io import download, query, reprocess, upload
from imap_data_access.processing_input import (
    AncillaryInput,
    ProcessingInputCollection,
    RepointInput,
    ScienceInput,
    SPICEInput,
    SpinInput,
)

__all__ = [
    "VALID_DATALEVELS",
    "VALID_INSTRUMENTS",
    "AncillaryFilePath",
    "AncillaryInput",
    "CadenceFilePath",
    "DependencyFilePath",
    "ImapFilePath",
    "ProcessingInputCollection",
    "QuicklookFilePath",
    "RepointInput",
    "SPICEFilePath",
    "SPICEInput",
    "ScienceFilePath",
    "ScienceInput",
    "SpinInput",
    "download",
    "query",
    "reprocess",
    "upload",
]

__version__ = importlib.metadata.version("imap-data-access")


config = {
    "DATA_ACCESS_URL": os.getenv("IMAP_DATA_ACCESS_URL")
    or "https://api.imap-mission.com",
    "DATA_DIR": Path(os.getenv("IMAP_DATA_DIR") or Path.cwd() / "data"),
    "API_KEY": os.getenv("IMAP_API_KEY"),
    "ACCESS_TOKEN": os.getenv("IMAP_ACCESS_TOKEN"),
    # Create a base64 encoded string for the username and password
    # echo -n 'username:password' | base64
    "WEBPODA_TOKEN": os.getenv("IMAP_WEBPODA_TOKEN"),
}
"""Settings configuration dictionary.

DATA_ACCESS_URL : This is the URL of the data access API.
DATA_DIR : This is where the file data is stored and organized by instrument and level.
    The default location is a 'data/' folder in the current working directory,
    "but this can be set on the command line using the --data-dir option, or through
    the environment variable IMAP_DATA_DIR.
API_KEY : This is the API key used to authenticate with the data access API.
    It can be set on the command line using the --api-key option, or through the
    environment variable IMAP_API_KEY. It is only necessary for uploading files.
WEBPODA_TOKEN : This is the token used to authenticate with the webpoda API.
    It can be set on the command line using the --webpoda-token option, or through
    the environment variable IMAP_WEBPODA_TOKEN. It is only necessary for downloading
    packet data.
"""


# NOTE: ialirt and spacecraft aren't actual instruments, but they are
#       additional data sources for packet definitions and processing
VALID_INSTRUMENTS = {
    "codice",
    "glows",
    "hit",
    "hi",
    "ialirt",
    "idex",
    "lo",
    "mag",
    "spacecraft",
    "swapi",
    "swe",
    "ultra",
}

VALID_DATALEVELS = {
    "l0",
    "l1",
    "l1a",
    "l1b",
    "l1c",
    "l1ca",
    "l1cb",
    "l1d",
    "l2",
    "l2a",
    "l2b",
    "l2c",
    "l3",
    "l3a",
    "l3b",
    "l3c",
    "l3d",
    "l3e",
}

VALID_TABLES = {
    "science",
    "ancillary",
    "spice",
}
