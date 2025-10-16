'''
Created on 15-06-2013

@author: ahypki
'''

import sys
from builtins import Exception

def assertTrue(condition, msg):
    if condition is False:
        raise Exception("Assertion failed", msg)