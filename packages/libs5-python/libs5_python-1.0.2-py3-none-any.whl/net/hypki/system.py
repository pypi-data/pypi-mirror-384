'''
Created on 18-07-2013

@author: ahypki
'''

import inspect
import os.path
import re
import subprocess
import sys
import time
import urllib.request


def getThisScriptPath():
    return inspect.stack()[1][1] # inspect.getfile(inspect.currentframe()) # script filename (usually with path)


def getThisScriptDirectory():
    return os.__path.dirname(os.__path.abspath(inspect.stack()[1][1])) # script directory


def getSystemVariable(name):
    for param in os.environ.keys():
        if param == name:
            return os.environ[param]
    return None