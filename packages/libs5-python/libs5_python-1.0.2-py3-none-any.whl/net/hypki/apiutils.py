'''
Created on Aug 15, 2025

@author: ahypki
'''
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

def streamGET(url, params):
    s = requests.Session()
    return s.get(url, params=params, headers=None, stream=True).iter_lines()
#    with s.get(url, params=params, headers=None, stream=True) as resp:
#        for line in resp.iter_lines():
#            if line:
#                print(line)

def streamPOST(url, file, params):
    # s = requests.Session()
    # Specify the content type
    # headers = {'Content-Type': 'application/octet-stream'}
    # headers = {'Content-Type': 'multipart/form-data'}
    # return s.post(url, headers=headers, data=stream)
    fields = params
    fields['file'] = (file, open(file, 'rb'), 'text/plain')
    multipart_data = MultipartEncoder(
        fields=fields
    )
    return requests.post(url,
                         data=multipart_data,
                         headers={'Content-Type': multipart_data.content_type}, 
                         timeout=30)

