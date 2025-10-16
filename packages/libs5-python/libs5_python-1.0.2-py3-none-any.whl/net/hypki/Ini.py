'''
Created on Oct 15, 2025

@author: ahypki
'''
import ini
import re

class Ini(object):
    '''
    classdocs
    https://pypi.org/project/ini-parser/
    '''
    __path = None
    __iniLines = None

    def __init__(self, path):
        '''
        Constructor
        '''
        self.__path = path
        
    def __getIni(self):
        if self.__iniLines is None:
            self.__iniLines = open(self.__path, "r").readlines()
                
        return self.__iniLines
    
    def __isKey(self, line):
        k = self.__getKey(line)
        return False if k is None else True
    
    def __getKey(self, line):
        m = re.match("^[\s]*(\w[\w\d]*)[\s]*=[\s]*.*$", line)
        if m:
            return m.group(1)
        return None
    
    def __isSection(self, line):
        sec = self.__getSection(line)
        return False if sec is None else True
    
    def __getSection(self, line):
        m = re.match("^[\s]*\[(\w[\w\d]+)\][\s]*$", line)
        if m:
            return m.group(1)
        return None
        
    def getSections(self):
        sections = []
        for line in self.__getIni():
            if self.__isSection(line):
                sections.append(self.__getSection(line))
        return sections
    
    def getKeys(self, section):
        keys = []
        currentSection = None
        for line in self.__getIni():
            if self.__isSection(line):
                currentSection = self.__getSection(line)
                continue
            if self.__isKey(line):
                if currentSection is not None and currentSection == section:
                    keys.append(self.__getKey(line))
        return keys
    
    def set(self, section, key, value):
        newLines = []
        currentSection = None
        for line in self.__getIni():
            lineAdded = False
            
            if self.__isSection(line):
                currentSection = self.__getSection(line)
                
            if self.__isKey(line):
                currentKey = self.__getKey(line)
                if currentSection is not None and currentSection == section and currentKey == key:
                    newLines.append(key + " = " + value)
                    lineAdded = True
                    
            if not lineAdded:
                newLines.append(line)
                
        self.__iniLines = newLines
        
    def get(self, section, key):
        currentSection = None
        for line in self.__getIni():
            if self.__isSection(line):
                currentSection = self.__getSection(line)
                continue
            if self.__isKey(line):
                currentKey = self.__getKey(line)
                if currentSection is not None and currentSection == section and currentKey == key:
                    return line[(line.index("=") + 1):].strip()
        return None
        
    def save(self):
        if self.__iniLines is not None:
            with open(self.__path, 'w') as f:
                for line in self.__iniLines:
                    f.write(f"{line.strip()}\n")
