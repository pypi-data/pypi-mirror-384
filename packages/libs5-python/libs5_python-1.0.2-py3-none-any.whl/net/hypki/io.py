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
from net.hypki.regex import *
from net.hypki.log import *

def absolutePath(path):
    return os.__path.abspath(path)

def findFolders(path):
    dirsAll = []
    for dirName, dirs, files in os.walk(path):
        dirsAll.append(dirName)
#         path = root.split('/')
#         print (len(path) - 1) *'---' , os.path.basename(root)       
#         for file in files:
#             print len(path)*'---', file
    return dirsAll

def readString( prompt ):
    print(bcolors.OKBLUE + prompt + bcolors.ENDC, end = '', flush = True)
    return sys.stdin.readline().strip()

def linux_cmd(cmd, workingDir = None, printImmediatelly = False):
    if printImmediatelly:
        debug("linux cmd: " + cmd);
    result = []
    s = subprocess.Popen(cmd, cwd = workingDir, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    for line in s.stdout.readlines():
        strLine = str(line).rstrip()
#         if printImmediatelly is False:
        result.append(firstGroup(strLine, 'b\'(.*)\\\\n\''))
#         else:
        if printImmediatelly:
            print(firstGroup(strLine, 'b\'(.*)\\\\n\''))
    return result

def linux_cmd_fork(cmd):
#     info("linux cmd fork: " + cmd);
    os.system(cmd)

def is_file_exists(path):
    return os.path.exists(path)

def url_read(url):
    resp = urllib.request.urlopen(url)
    return resp.read().decode('utf-8')

def read_file(path):
    with open(path, 'r') as content_file:
        return content_file.read()
    
def append_to_file(path, line):
    with open(path, 'a') as content_file:
        content_file.write('\n')
        content_file.write(line)
    
def file_save(path, content):
    myFile = open(path, 'w', encoding = 'UTF8')
    myFile.write(content)
    myFile.close()
    