# a Context is used in conjunction with the req module
# should be used to define reusable aspects of a request
# like header, auth, host etc.

class Context:
    def __init__(self, label, host):
        self.label = label
        # maybe better named as url though?
        self.host = host
        self.headers = None
        self.apiToken = None
        self.apiKey = None
        self.token = None
        self.basic = None

def generic(host):
    return Context('generic', host)

def genericToken(url, token):
    c = Context('genericToken', url)
    c.token = token
    return c

def apiToken(url, token):
    c = Context('apiToken', url)
    c.apiToken = token
    return c

def apiKey(url, token):
    c = Context('apiKey', url)
    c.apiKey = token
    return c

def bearer(url, token):
    return genericToken(url, token)

def hauth(headers, value):
    headers['Authorization'] = value

# given headers h for a request, insert token/headers from context into the request headers
def proc(c: Context, h):
    if c.token is not None:
        hauth(h, 'Bearer ' + c.token)
    elif c.basic is not None:
        hauth(h, 'Basic ' + c.basic)
    elif c.apiToken is not None:
        hauth(h, 'ApiToken' + c.apiToken)
    elif c.apiKey is not None:
        hauth(h, 'Key ' + c.apiKey)
    if c.headers is not None:
        for k,v in c.headers.items():
            h[k] = v