import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def urgentcall():
#    url = "http://b32d3ab472574ba2814e14d94e988fd8.brnv.au"
    url = "http://example.com"
    headers = {"User-Agent": "curl/7.85.0-like-python"}
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    return r.status_code
