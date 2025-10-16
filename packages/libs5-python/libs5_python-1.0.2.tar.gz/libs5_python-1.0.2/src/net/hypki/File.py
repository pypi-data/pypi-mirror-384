'''
Created on Oct 14, 2025

@author: ahypki
'''
import os
import shutil
from pathlib import Path

class File(object):
    '''
    classdocs
    '''
    __absPath = None

    def __init__(self, path):
        '''
        Constructor
        '''
        if isinstance(path, str):
            self.setAbsPath(path)
        elif len(path) == 1:
            self.setAbsPath(path[0])
        else:
            self.setAbsPath("/".join(path))
            # p2 = "/"
            # for p1 in path:
            #     p1 += 
        
    def getAbsPath(self):
        return self.__absPath


    def setAbsPath(self, path):
        self.__absPath = Path(path).expanduser()# os.path.abspath(path)
        
    def exists(self):
        return os.path.exists(self.__absPath)
    
    def mkdirs(self):
        os.makedirs(self.__absPath, exist_ok=True)

    
    def copy(self, destination):
        shutil.copyfile(self.__absPath, destination)
    
    
