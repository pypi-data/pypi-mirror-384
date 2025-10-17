#! /usr/bin/env python3
# 
# Miscellanous utilities for ipython usage
#
# Note:
# - This is idiosyncractic code based on Tom O'Hara's ipython startup file
#   (~/.ipython/profile_default/startup/25-quarter.py).
# - To faciliate importing functions and variables for testing purposes (e.g., EX tests),
#   use import_module_globals as illustrated in second example below.
#

"""
Adhoc stuff for ipython (or Jupyter notebooks)

Simple usage:
    from mezcla.ipython_utils import *

Advanced usage:
    # Make sure import-globals utility active
    import mezcla.ipython_utils
    reload(mezcla.ipython_utils)
    import_module_globals = mezcla.ipython_utils.import_module_globals

    # Run over misc_utils.py
    import_module_globals("mezcla.misc_utils", globals_dict=builtins.globals())
    #
    # note: ipython chokes over the following when preceding comment included:
    # >>> (TYPICAL_EPSILON, VALUE_EPSILON)
    # (1e-06, 0.001)

Misc. usage:
    set_xterm_title("ipython: " + os.getcwd())
"""

# Note: most imports are done for the sake of ipython usage
#
# pylint: disable=unused-import

# Standard modules
import builtins
from collections import defaultdict, namedtuple
import json
import math
import os
import random
import re
import sys
from importlib import reload

# Installed modules
try:
    import nltk
    import numpy as np
    import pandas as pd
    import sklearn
except:
    nltk = np = pd = sklearn = None
    sys.stderr.write(f"Exception during installed imports: {sys.exc_info()}")

# Local local modules
import mezcla
from mezcla import debug
from mezcla import html_utils
from mezcla.main import Main
from mezcla import system
from mezcla.my_regex import my_re
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo
try:
    from mezcla import data_utils as du
    from mezcla.unittest_wrapper import TestWrapper
except:
    du = TestWrapper = None
    system.print_exception_info("loading local modules with dependencies")

# Constants
TL = debug.TL

# Environment options
HOME = gh.HOME_DIR
USER = system.USER

#-------------------------------------------------------------------------------
# Global Variables
#
# Note:
# - intended to faciliate experimentation in ipython
# - crytic names for historical reasons (and since hash and list reserved words)
#

h = {'a': 1, 'b': 2, 'c': 3}
l = [1, 2, 3]
t = "some text"
text = t
try:
    english_stopwords = nltk.corpus.stopwords.words('english')
    spanish_stopwords = nltk.corpus.stopwords.words('spanish')
except:
    system.print_exception_info("loading resources like NLTK")
  
#-------------------------------------------------------------------------------
# Helper functions

def grep_obj_methods(obj, pattern, flags=None):
    """Return methods for OBJ matching PATTERN (with optional re.search FLAGS)
    Note: in practice, all object members are grepped"""
    ## TODO3: rename as grep_obj_attributes
    # EX: grep_obj_methods(str, "strip") => ["lstrip", "strip", "rstrip"]
    if flags is None:
        flags = re.IGNORECASE
    return list(m for m in dir(obj) if re.search(pattern, m, flags))


def import_module_globals(module_name, include_private=False, include_dunder=False, globals_dict=None, ignore_errors=None):
    """Import MODULE_NAME optionally with INCLUDE_PRIVATE and INCLUDE_DUNDER and setting GLOBALS_DICT"""
    debug.trace_expr(5, module_name, include_private, include_dunder, globals_dict, ignore_errors,
                     prefix="in import_module_globals: ")
    # note: intended to support reloading modules imported in ipython via 'from module import *'
    # TODO3: find a cleaner way of doing this (e.g., via import support)
    # EX: import_module_globals("mezcla.misc_utils", globals_dict=builtins.globals()); VALUE_EPSILON => 1e-3
    # pylint: disable=eval-used, exec-used
    if globals_dict is None:
        globals_dict = builtins.globals()
    if ignore_errors is None:
        ignore_errors = False
    
    # Ensure module_name is a string
    if not isinstance(module_name, str):
        if not ignore_errors:
            system.print_error(f"Error: module_name must be a string, got {type(module_name)}")
        debug.trace(5, f"module_name is not a string: {type(module_name)}")
        return
    
    # Get list of modules attributes (e.g., variables)
    module = None
    module_attrs = []
    try:
        debug.trace(7, "in try")
        loaded = False
        
        # Check if module already exists in sys.modules
        module_exists = module_name in sys.modules
        
        if module_exists:
            try:
                debug.trace(6, "Module exists - trying reload")
                # First import it into the namespace if not already there
                import_command = f"import {module_name}"
                exec(import_command, globals_dict)
                module = eval(module_name, globals_dict)
                module = reload(module)
                loaded = True
            except:
                debug.trace_exception_info(7, "existing reload")
        
        if not loaded:
            try:
                debug.trace(5, "Trying import")
                import_command = f"import {module_name}"
                exec(import_command, globals_dict)
                module = eval(module_name, globals_dict)
                loaded = True
            except:
                debug.trace_exception_info(4, f"{module_name} import")
        
        if loaded:
            module_attrs = dir(module)
        elif not ignore_errors:
            system.print_error(f"Error: unable to import or reload {module_name}")
    except:
        if not ignore_errors:
            system.print_exception_info("import_module_globals")
        else:
            debug.trace_exception_info(6, "import_module_globals")
    debug.trace_expr(5, module)

    # Import each individually
    num_ok = 0
    num_ignored = 0
    for var in module_attrs:
        debug.trace_expr(6, var)

        # Optionally, include "dunder" attributes like __name__ or private ones like _name
        include = True
        if var.startswith("__"):
            if not include_dunder:
                include = False
                debug.trace(7, f"excluding dunder attribute {var!r}")
        elif (var.startswith("_") and not include_private):
            include = False
            debug.trace(7, f"excluding private attribute {var!r}")

        # Import the value
        if include:
            import_desc = (f"import[ing] {var} from {module_name}")
            try:
                debug.trace(5, import_desc)
                globals_dict[var] = getattr(module, var)
                num_ok += 1
            except:
                debug.trace_exception_info(4, import_desc)
        else:
            num_ignored += 1
    debug.trace(5, f"{num_ok} of {len(module_attrs)} attributes loaded OK; {num_ignored=}")
    return


def pr_dir(obj):
    """Print dir listing for OBJ"""
    print(dir(obj))


def set_xterm_title(title=None):
    """Set xterm TITLE via set_xterm_title.bash
    Note:
    - Uses set_xterm_title.bash from https://github.com/tomasohara/shell-scripts.
    - The TITLE can use environment variables (e.g., "ipython [$CONDA_PREFIX]").
    """
    # Sample result: "ipython: /home/tomohara/mezcla: Py3.10(base)"
    if title is None:
        title = "ipython $PWD"
    gh.issue(f'set_xterm_title.bash "{title}"')
    
#-------------------------------------------------------------------------------
# Helper class

class Fubar():
    """Dummy class used for cut-n-paste of method code (e.g., under ipython)
    Example:
      # setup
      debug.assertion("Fubar" in str(self))
      self.dummy_arg = True
      # cut-n-pasted code (see template.py_
      debug.trace_object(1, self, label=f"{self.__class__.__name__} instance")
    Output:
      Fubar instance: {
          dummy_arg: True
          }
    """
    pass

#-------------------------------------------------------------------------------
# Initialization
# note: self and dummy_main are for interactive usage

self = Fubar()


dummy_main = Main([])

#-------------------------------------------------------------------------------
    
def main() -> None:
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone\n")
    _main_app = Main(description=__doc__.format(script=gh.basename(__file__)))


if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
