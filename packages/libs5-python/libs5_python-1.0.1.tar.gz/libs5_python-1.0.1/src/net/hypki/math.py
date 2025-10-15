
import subprocess
import sys
import re
import os
from net.hypki.io import *
from net.hypki.args import *

def math_eval(s):
    try:
        return eval(s)
    except SyntaxError:
        return 0