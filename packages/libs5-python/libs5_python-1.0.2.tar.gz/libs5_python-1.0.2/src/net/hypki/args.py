'''
Created on 15-06-2013

@author: ahypki
'''

import sys

class ArgUtils:

    def getString(name, defaultvalue):  # @NoSelf
        for i in range(len(sys.argv)):
            if sys.argv[i] == "--" + name or sys.argv[i] == "-" + name:
                return sys.argv[i + 1].strip()
        return defaultvalue
    
    def isArgPresent(name):  # @NoSelf
        for i in range(len(sys.argv)):
            if sys.argv[i] == "--" + name or sys.argv[i] == "-" + name:
                return True
        return False