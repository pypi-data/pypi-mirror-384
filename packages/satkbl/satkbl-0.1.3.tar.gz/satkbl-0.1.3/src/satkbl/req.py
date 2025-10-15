import warnings
from http.cookies import SimpleCookie

import requests

import util as u
import ctx

# consts for content types
t_html = 'text/html'
t_json = 'application/json'
t_form = 'application/x-www-form-urlencoded'

# class to hold response data
class ResponseObj:
    def __init__(s):
        s.r = None
        s.data = None
        s.text = None
        s.cookies = {}
        s.headers = None
        s.status = None

# GET a specific type
def gett(c, path, type):
    headers = {
        'Accept': type
    }
    ctx.proc(c, headers)
    url = c.host + path
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        r = requests.get(url, headers=headers, verify=False)
    return r

# process response
def procResponse(response):
    ro = ResponseObj()
    ro.r = response
    ro.status = response.status_code
    ro.headers = dict(response.headers)
    cookieStr = response.headers.get('Set-Cookie')
    cookieStr = fixCookieExpires(cookieStr)
    if cookieStr is not None:
        cookies = SimpleCookie()
        cookies.load(cookieStr)
        for k,v in cookies.items():
            ro.cookies[k] = v
    return ro

# fix cookie expires
def fixCookieExpires(cookieStr):
    if cookieStr is None:
        return None
    parts = cookieStr.split(';')
    parts2 = []
    for part in parts:
        partNew = ''
        needsQuote = False
        if 'Expires=' in part and not 'Expires="' in part:
            partNew = part.replace('Expires=','Expires="')
            needsQuote = True
        elif 'expires=' in part and not 'expires="' in part:
            partNew = part.replace('Expires=','Expires="')
            needsQuote = True

        if needsQuote:
            partNew = partNew + '"'
            parts2.append(partNew)
        else:
            parts2.append(part)
    r = ';'.join(parts2)
    return r

# POST specific type request/response
def postt(c, path, data, requestType, responseType):
    headers = {
        'Content-Type': requestType,
        'Accept': responseType
    }
    ctx.proc(c, headers)
    url = c.host + path
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        r = requests.post(url, headers=headers, data=data, verify=False)
    return r

# PUT specific type request/response
def putt(c, path, data, requestType, responseType):
    headers = {
        'Content-Type': requestType,
        'Accept': responseType
    }
    ctx.proc(c, headers)
    url = c.host + path
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        r = requests.put(url, headers=headers, data=data, verify=False)
    return r

# PATCH specific type request/response
def patcht(c, path, data, requestType, responseType):
    headers = {
        'Content-Type': requestType,
        'Accept': responseType
    }
    ctx.proc(c, headers)
    url = c.host + path
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        r = requests.patch(url, headers=headers, data=data, verify=False)
    return r

# GET json
def getj(c, path):
    r = gett(c, path, t_json)
    ro = procResponse(r)
    try:
        ro.data = r.json()
    except requests.exceptions.JSONDecodeError:
        u.l('ERROR: convering response to json')
        u.l(f'response = {r.text}')
    return ro

# GET html
def geth(c, path):
    r = gett(c, path, t_html)
    ro = procResponse(r)
    ro.data = r.text
    return ro

# POST form, get json
def postfj(c, path, data):
    r = postt(c, path, data, t_form, t_json)
    ro = procResponse(r)
    try:
        ro.data = r.json()
    except requests.exceptions.JSONDecodeError:
        u.l('ERROR: convering response to json')
        u.l(f'response = {r.text}')
    return ro

# POST form, get html
def postfh(c, path, data):
    r = postt(c, path, data, t_form, t_html)
    ro = procResponse(r)
    ro.data = r.text
    return ro

# POST text, get json
def posthj(c, path, data):
    r = postt(c, path, data, t_html, t_json)
    ro = procResponse(r)
    try:
        ro.data = r.json()
    except requests.exceptions.JSONDecodeError:
        u.l('ERROR: convering response to json')
        u.l(f'response = {r.text}')
    return ro

# POST json, get json
def postjj(c, path, data):
    data = u.mtoj(data)
    r = postt(c, path, data, t_json, t_json)
    ro = procResponse(r)
    try:
        ro.data = r.json()
    except requests.exceptions.JSONDecodeError:
        u.l('ERROR: convering response to json')
        u.l(f'response = {r.text}')
    return ro

# PUT json, get json
def putjj(c, path, data):
    data = u.mtoj(data)
    r = putt(c, path, data, t_json, t_json)
    ro = procResponse(r)
    try:
        ro.data = r.json()
    except requests.exceptions.JSONDecodeError:
        u.l('ERROR: convering response to json')
        u.l(f'response = {r.text}')
    return ro

# PATCH json, get json
def patchjj(c, path, data):
    data = u.mtoj(data)
    r = patcht(c, path, data, t_json, t_json)
    ro = procResponse(r)
    try:
        ro.data = r.json()
    except requests.exceptions.JSONDecodeError:
        u.l('ERROR: convering response to json')
        u.l(f'response = {r.text}')
    return ro

# POST multi
def postMulti(c, path, data):
    headers = {}
    ctx.proc(c, headers)
    url = c.host + path
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        r = requests.post(url, headers=headers, files=data, verify=False)
    return r

# DELETE
def delete(c, path):
    headers = {}
    ctx.proc(c, headers)
    url = c.host + path
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        r = requests.delete(url, headers=headers, verify=False)
    ro = procResponse(r)
    return ro
