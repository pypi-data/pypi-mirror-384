"""Base constant values for the NIBCQ project."""

import os

# Path constants

# Path to the Public Documents.
PUBLIC_DOCUMENTS_PATH = os.path.join(os.environ["PUBLIC"], "Documents")

TOOLKIT_FOLDER_PATH = os.path.join(
    PUBLIC_DOCUMENTS_PATH, "National Instruments", "NI-Cell Quality Toolkit"
)
"""str: Path to the NI-Cell Quality Toolkit folder."""

DEFAULT_COMPENSATION_DIR = os.path.join(TOOLKIT_FOLDER_PATH, "Compensation")
"""str: Default folder where compensation files are stored."""
