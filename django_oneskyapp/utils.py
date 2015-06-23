import hashlib
import os
import requests
import time
import warnings


warnings.filterwarnings("ignore", message=".*InsecurePlatformWarning.*")

"""
    
    OneSky's simple python wrapper
    
    Known WTF?:
    - If you manualy create project file (e.g. django.po) inside SkyOne app, API will return 400 error "This file is not downloadable through API"
    - Always upload at least your default django.po language file for each project. 
    
"""

class OneSkyApiClient(object):
    
    def __init__(self, api_key, api_secret, locale_path='.'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.locale_path = locale_path
        pass
        
    def json_request(self, method = "get", api_path = None, api_params = None, file_stream = None):
        url = 'https://platform.api.onesky.io/1/' + api_path
        url_params = {}
        if isinstance(api_params, dict):
            url_params = dict([(k, v) for k, v in api_params.items() if v is not None])
        
        timestamp = str(int(time.time()))
        auth_hash = hashlib.md5()
        auth_hash.update(timestamp)
        auth_hash.update(self.api_secret)
        url_params["dev_hash"] = auth_hash.hexdigest()
        url_params["timestamp"] = timestamp
        url_params["api_key"] = self.api_key
        
        if method.lower() == "get":
            response = requests.get(url, params=url_params)
        elif method.lower() == "post":
            file_name = url_params["file_name"]
            del url_params["file_name"]
            response = requests.post(url, params=url_params, files={"file":(file_name,file_stream)} if file_stream else None)
        
        if(response.headers.get('content-disposition', '').startswith('attachment;')):
            filename = response.headers['content-disposition'].split('=')[1]
            dest_filename = os.path.join(self.locale_path, filename)
            try:
                os.makedirs(os.path.dirname(dest_filename))
            except OSError,e:
                # Ok if path exists
                pass
            with open(dest_filename, 'wb') as f:
                for chunk in response.iter_content():
                    f.write(chunk)
            response_output = {'filename': dest_filename}
        else:
            try:
                response_output = response.json()
            except ValueError:
                response_output = {}
        
        return response.status_code, response_output
    
    def json_get_request(self, *args, **kwargs):
        return  self.json_request(method = "get", *args, **kwargs)
    def json_post_request(self, *args, **kwargs):
        return  self.json_request(method = "post", *args, **kwargs)
    
    def project_languages(self, project_id):
        return self.json_get_request(api_path="projects/%s/languages" % project_id)
        
    def file_list(self, project_id, page=1):
        return self.json_get_request(api_path="projects/%s/files" % project_id, api_params={"page":page})
        
    def file_upload(self, project_id, file_name, file_format = "GNU_PO", locale = None, is_keeping_all_strings=None):
        with open(file_name, 'rb') as file_stream:
            return self.json_post_request(api_path="projects/%s/files" % project_id, file_stream=file_stream, api_params={"file_name":os.path.basename(file_name), "file_format":file_format, "locale":locale, "is_keeping_all_strings":is_keeping_all_strings})
            
    def translation_export(self, project_id, locale, source_file_name, export_file_name):
        return self.json_get_request(api_path="projects/%s/translations" % project_id, api_params={"locale":locale, "source_file_name": source_file_name , "export_file_name": export_file_name})

class OneSkyApiClientException(Exception):
    pass
