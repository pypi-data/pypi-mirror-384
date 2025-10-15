'''
Created on 08-05-2013

@author: ahypki
'''

import os.path
import re
import subprocess
import sys
import time
import urllib.request

TRACE = False
DEBUG = True
INFO = True

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    RED = '\033[91m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.RED = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''
        
def green( msg ):
    print(bcolors.OKGREEN + str(msg) + bcolors.ENDC)
    return

def blue( msg ):
    print(bcolors.OKBLUE + msg + bcolors.ENDC)
    return

def red( msg ):
    print(bcolors.RED + msg + bcolors.ENDC)
    return

def msg( msg ):
    print(bcolors.OKBLUE + msg + bcolors.ENDC)
    return

def trace( parameters ):
    if (TRACE):
        print("TRACE  " + parameters)
    return

def debug(parameters, printLogLevel = True, printNewLine = True):
    if (DEBUG):
        print(("DEBUG " if printLogLevel else '') + str(parameters), end = ('\n' if printNewLine else ''))
    return

def log( parameters ):
    debug(parameters)

def info( parameters, printLogLevel = True, printNewLine = True):
    if (INFO):
        print(("INFO  " if printLogLevel else '') + str(parameters), end = ('\n' if printNewLine else ''))
    return

def warn(parameters, printLogLevel = True, printNewLine = True):
    print(bcolors.WARNING + "WARN   " + str(parameters) + bcolors.ENDC)
    return

def error( parameters, printLogLevel = True, printNewLine = True, end = '' ):
    print(bcolors.FAIL + "ERROR   " + str(parameters) + bcolors.ENDC, end, file=sys.stderr)
    return