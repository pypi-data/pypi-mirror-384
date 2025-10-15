'''
Created on 18-07-2013

@author: ahypki
'''

import os
import uuid
import base64

def nextUuid():
    return str(uuid.uuid4())
#     r_uuid = base64.urlsafe_b64encode(uuid.uuid4().bytes)
#     return str(r_uuid.replace('=', ''))