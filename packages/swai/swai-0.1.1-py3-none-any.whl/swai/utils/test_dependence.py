from swai.utils.log import logger
import os
import sys

def test_dependence():
    logger.info("Testing dependence...")
    try:
        import requests
    except ImportError:
        logger.error("requests not found, try to install with `pip install requests`")
        exit(1)
    try:
        import tabulate
    except ImportError:
        logger.error("tabulate not found, try to install with `pip install tabulate`")
        exit(1)
    try:
        import numpy
    except ImportError:
        logger.error("numpy not found, try to install with `pip install numpy`")
        exit(1)
    try:
        import AutoDockTools
    except ImportError:
        logger.error("AutoDockTools not found, try to install with `python -m pip install git+https://github.com/Valdes-Tresanco-MS/AutoDockTools_py3`")
        exit(1)
    try:
        from openbabel import openbabel
    except ImportError:
        logger.error("openbabel not found, try to install with `conda install openbabel` or `conda install openbabel -c conda-forge`")
        exit(1)
    logger.info("All dependence found")