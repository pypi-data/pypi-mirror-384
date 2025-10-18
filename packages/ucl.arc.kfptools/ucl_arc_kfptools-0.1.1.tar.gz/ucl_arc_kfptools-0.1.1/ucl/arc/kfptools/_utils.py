"""Internal utilities for the kfptools package."""

import os
import json


def _load_context():
    """Load the KFP context from the local configuration file.

    Returns:
        dict: The loaded context data.

    Raises:
        Exception: If the context.json file is not found.
    """
    context_path = os.path.expanduser("~/.config/kfp/context.json")
    if os.path.exists(context_path):
        with open(context_path, "r") as f:
            context = json.load(f)
        return context, context_path
    else:
        error_msg = f"context.json not found at expected path: {context_path}"
        raise Exception(error_msg)
