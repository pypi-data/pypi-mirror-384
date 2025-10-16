'''
Created on 08-05-2013

@author: ahypki
'''

from net.hypki import *
import os.path
import re
import subprocess
import sys
import time
# import urllib.request

def replace(string, searchPattern, replacement):
    return re.sub(searchPattern, replacement, string, count=0, flags=0)

def firstGroup(s, regex):
    r = re.compile(regex)
    m = r.search(s)
    if m:
        return m.group(1)
    return ""

def allGroups(s, regex):
    r = re.compile(regex)
    m = r.search(s)
    if m:
        return m.groups()
    return ""

def isLong(strNumber):
    return matches(strNumber, "^[\d]+$")
    
def isDouble(strNumber):
    return matches(strNumber, "[\d]+\.[\d\+\-eE]+")

def matches(s, regex):
    r = re.compile(regex)
    m = r.search(s)
    if m:
        return True
    return False

def matchesIgnoreCase(s, regex):
    r = re.compile(regex, re.IGNORECASE)
    m = r.search(s)
    if m:
        return True
    return False