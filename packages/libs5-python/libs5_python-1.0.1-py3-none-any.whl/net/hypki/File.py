'''
Created on Oct 14, 2025

@author: ahypki
'''
import os

class File(object):
    '''
    classdocs
    '''
    __absPath = None

    def __init__(self, path):
        '''
        Constructor
        '''
        self.setAbsPath(path)
        
    def getAbsPath(self):
        return self.__absPath


    def setAbsPath(self, path):
        self.__absPath = os.path.abspath(path)
