# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""AzureML ACFT Image Components package."""
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import sys

try:
    from azureml.automl.core.shared import logging_utilities, log_server
except ImportError:
    logging_utilities = None
    log_server = None

try:
    from ._version import ver as VERSION, selfver as SELFVERSION
    __version__ = VERSION
except ImportError:
    VERSION = '0.0.0+dev'
    SELFVERSION = VERSION
    __version__ = VERSION

PROJECT_NAME = __name__

# Mark this package as being allowed to log certain built-in types
module = sys.modules[__name__]
if logging_utilities is not None:
    logging_utilities.mark_package_exceptions_as_loggable(module)
if log_server is not None:
    log_server.install_sockethandler(__name__)
