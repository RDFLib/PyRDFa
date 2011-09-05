#!/usr/bin/env python
"""
Run the pyRdfa package locally, ie, on a local file
"""
# You may want to adapt this to your environment...
import sys, getopt, platform

sys.path.insert(0,"/Users/ivan/Source/PythonModules/pyRdfa-3.0")

from pyRdfa import pyRdfa
from pyRdfa.ProfileCache import offline_cache_generation

uris = [
	"http://www.w3.org/2007/08/pyRdfa/profiles/sw-prefixes.ttl"
]

offline_cache_generation(uris)
