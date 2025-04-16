# -----------------------------------------------------------------------------
# Authors:     aric.sanders@nist.gov
# Created:     04/02/2025
# License:     NIST License
# -----------------------------------------------------------------------------
"""
experimental_design is a package for tools to create and manage
design of experiments (DOE), or statistical design of experiments

"""

#----------------------------------------------------------------------
# Standard Imports
import os
import sys

# -----------------------------------------------------------------------------
# Third Party Imports

# -----------------------------------------------------------------------------
# Module Constants
VERBOSE_IMPORT = True
TIMED_IMPORT = True
__version__ = "0.0.3"
"Constant that determines if import statements are echoed to output"
# The new module load scheme can be for module in DE_API_MODULES.keys()
# -----------------------------------------------------------------------------
DE_API_MODULES = {"experimental_design.experimental_designs":True}
"Dictionary that controls the definition of the API, this can be set to leave out any unwanted modules. Also it is" \
    "possible to discover all modules by DE_API_MODULES.keys()"

# This makes sure this file is the one loaded
sys.path.append(os.path.dirname(__file__))
# To tune the imported API change the DE_API_MODULES dictionary
if TIMED_IMPORT:
    import datetime

    first_timer = datetime.datetime.now(datetime.timezone.utc)
    start_timer = datetime.datetime.now(datetime.timezone.utc)
for module in sorted(DE_API_MODULES.keys()):
    try:
        if DE_API_MODULES[module]:
            if VERBOSE_IMPORT:
                print(("Importing {0}".format(module)))
            exec('from {0} import *'.format(module))
            if TIMED_IMPORT:
                end_timer = datetime.datetime.now(datetime.timezone.utc)
                time_difference = end_timer - start_timer
                print(("It took {0} s to import {1}".format(time_difference.total_seconds(), module)))
                start_timer = end_timer
    except Exception as e:
        print(f"The {module} failed to import")
        print(e)
        
if TIMED_IMPORT:
    end_timer = datetime.datetime.now(datetime.timezone.utc)
    time_difference = end_timer - first_timer
    print(("It took {0} s to import all of the active modules".format(time_difference.total_seconds())))
