#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 13:23:51 2025

@author: roman
"""

# scs/__init__.py
try:
    import swg.sw_procedure
except ImportError:
    raise ImportError(
        "⚠️ Missing dependency 'swg'.\n"
        "Please install with:\n\n"
        "    pip install swg --index-url https://dl.cloudsmith.io/public/cs-x033/swg/python/simple/\n"
    )
    
    
try:
    import ninatool.circuits.base_circuits
except ImportError:
    raise ImportError(
        "⚠️ Missing dependency 'swg'.\n"
        "Please refer to https://github.com/sandromiano/ninatool for NINA installation."
        "    pip install swg --index-url https://dl.cloudsmith.io/public/cs-x033/swg/python/simple/\n"
    )


