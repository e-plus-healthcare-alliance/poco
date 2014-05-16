import urllib
import urllib2
import urlparse
import json


class APIClient:
    def __init__(self, api_root):
        self.api_root = api_root

    def __call__(self, path, params, body=None, headers={}):
        full_url = urlparse.urljoin(self.api_root, path)
        if params:
            params_str = "?" + urllib.urlencode(params)
        else:
            params_str = ""
        full_url += params_str
        full_headers = {'Content-type': 'application/json'}
        full_headers.update(headers)
        if body:
            req = urllib2.Request(full_url, data=json.dumps(body), 
                                  headers=full_headers)
        else:
            req = urllib2.Request(full_url,
                                  headers=full_headers)

        content = urllib2.urlopen(req).read()
        result = json.loads(content)
        return result