import json
import time
import base64
import urllib.parse
import traceback
import random
import collections
import sys
import csv
import threading
import multiprocessing
import queue


utf8 = 'utf-8'

def test():
    print('hello from test function in baselayer module')


#----------------------------------------
# printing
#----------------------------------------

# pretty print dict as json
def pp(m):
    return json.dumps(m, indent=2)

# pretty print a json string
def ppj(j):
    return pp(jtom(j))

# convert dict to json string
def mtoj(m):
    return json.dumps(m)
    
# convert object to dict
def otom(o):
    return o.__dict__

# convert object to json
def otoj(o):
    return mtoj(otom(o))

# convert json string to a dict
def jtom(j):
    return json.loads(j)

# log shorthand
def l(t):
    print(t)

p = l

# log shorthand, no newline
def ln(t):
    print(t, end='')

# log pretty print obj
def lp(m):
    l(pp(m))

# log pretty print json string
def lpj(j):
    l(ppj(j))

# log a response
def lr(r):
    l('----------------------------------------')
    l('url = ' + r.r.url)
    l('status =  ' + str(r.status))
    l('headers = ')
    lp(dict(r.headers))
    l('cookies = ')
    for k,v in r.cookies.items():
        l(f'  {k} = {dict(v)}')

# log response obj with response data
def lrd(r):
    lr(r)
    lp(r.data)

# print stack trace
def lstack():
    traceback.print_exc()

#----------------------------------------
# rand
#----------------------------------------

# generate an id
def genId(prefix=''):
    return prefix + str(milliTime())

# get current time in millis
def milliTime():
    return round(time.time() * 1000)

# now time in millis
def now():
    return milliTime()

#random choice between bottom and top, half open, so up to, but not including top
def rchoice(bottom, top):
    return random.choice(range(bottom, top))

#----------------------------------------
# data structures
#----------------------------------------

# blank Object class to be used like a map
class BlankObj:
    pass

def obj():
    return BlankObj()

# init array to a specific size
def initArray(size):
    return [None for i in range(size)]

ia = initArray

# given a value, get the string type name for it
def valToType(val):
    if isinstance(val, int):
        return 'integer'
    elif isinstance(val, float):
        return 'float'
    elif isinstance(val, complex):
        return 'complex'
    elif isinstance(val, str):
        return 'string'
    elif isinstance(val, list):
        return 'list'
    elif isinstance(val, tuple):
        return 'tuple'
    elif isinstance(val, dict):
        return 'dictionary'
    elif isinstance(val, set):
        return 'set'
    elif isinstance(val, bool):
        return 'boolean'
    elif val is None:
        return 'None'
    else:
        return 'other'

# create a named tuple
def nt(name, list):
    return collections.namedtuple(name, list)

#----------------------------------------
# base64 
#----------------------------------------

# base64 decode encoded text to a byte array
def b64d(text):
    return base64.b64decode(text)

# base64 encode string to encoded string (rather than encoded bytes)
def b64e(val):
    return base64.b64encode(bytes(val, utf8)).decode(utf8)

# base64 url encode bytes
def b64ueb(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode(utf8)

# base64 url decode string to string
def b64ud(s):
    return base64.urlsafe_b64decode(s).decode(utf8)

# base64 encode bytes to encoded string
def b64eb(b):
    return base64.b64encode(b).decode(utf8)

#----------------------------------------
# web
#----------------------------------------

# url decode
def urld(u):
    return urllib.parse.unquote(u)

# url encode
def urle(u):
    return urllib.parse.quote(u)

# parse jwt
def parseJwt(jwt):
    vals = jwt.split('.')
    token = obj()
    token.header = jtom(b64d(vals[0]))
    token.body = jtom(b64d(vals[1]))
    token.sig = vals[2]
    return token

# print jwt
def printJwt(jwt):
    lp(jwt.header)
    lp(jwt.body)
    l(jwt.sig)

# create sample jwt with fake sig of just 0
# pass in the bodyFunc to mutate the body that's passed in to it
def jwt(bodyFunc=None):
    header0 = {
        'alg': 'RS256',
        'typ': 'JWT',
        'kid': 'key0'
    }
    body0 = {
        'nbf': time.time() - 3600,
        'iat': time.time() - 60,
        'exp': time.time() + 3600
    }
    if bodyFunc is not None:
        bodyFunc(body0)
    header = b64e(mtoj(header0))
    body = b64e(mtoj(body0))
    tokenWithoutSig = f'{header}.{body}'
    tokenSig = '0'
    tokenComplete = f'{tokenWithoutSig}.{tokenSig}'
    return tokenComplete

#----------------------------------------
# cli
#----------------------------------------

# check if we should run module as cli
def cli(name):
    if name == '__main__':
        return True
    return False

# get command line param at given index
def clpi(index):
    return sys.argv[index]

# execute function at dict val corresponding to key value
def execIfValid(option, optionDict):
    f = optionDict.get(option, None)
    f() if f is not None else p(f'error - invalid option {option}')

#----------------------------------------
# file
#----------------------------------------

# convert file at path to list of lines
def fileToLines(path):
    with open(path) as f:
        return f.readLines()
    
# convert file to a single string
def fileToString(path):
    with open(path) as f:
        return f.read()
    
# convert json file to dict
def fileToObj(path):
    with open(path, 'r') as jsonFile:
        return json.load(jsonFile)
    
# write a list of lines to a file
def linesToFile(path, lines):
    with open(path, 'w') as f:
        f.writeLines(lines)

# read csv to lines, skipping the header row
def readCsv(path, skip=True):
    csvRows = []
    with open(path, newline="") as csvFile:
        csvReader = csv.reader(csvFile)
        if skip:
            next(csvReader)
        for row in csvReader:
            csvRows.append(row)
    return csvRows

# read csv to lines with headers
def readCsvWithHeaders(path):
    return readCsv(path, False)

# write array of arrays to csv file
def writeCsv(path, lists):
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file)
        for row in lists:
            writer.writerow(row)

#----------------------------------------
# threading
#----------------------------------------

# sleep in seconds, can pass in float for smaller intervals
def sleep(seconds):
    time.sleep(seconds)

# struct for job result
class JobResult:
    def __init__(s, id, result):
        s.id = id
        s.result = result

def ioPool(func, args):
    return parallelPool(func, args,
                        lambda: queue.Queue(),
                        lambda x,y: threading.Thread(target=x, args=y))

def ioSingle(func, args):
    return parallelPool(func, args,
                        lambda: queue.Queue(),
                        lambda x,y: threading.Thread(target=x, args=y))[0]

def cpuPool(func, args):
    return parallelPool(func, args,
                        lambda: multiprocessing.Queue(),
                        lambda x,y: multiprocessing.Process(target=x, args=y))

# multi process
# func - the function to perform in prallel
# args - the list of args, one for each job, will be passed to the func
# resultGenFunc - ?
# threadGenFunc -?
# returns the results array
def parallelPool(func, args, resultGenFunc, threadGenFunc):
    jobCount = len(args)
    results = resultGenFunc()
    threads = []
    # create all threads and start them
    for i in range(jobCount):
        p = threadGenFunc(func, (i, args[i], results))
        threads.append(p)
        p.start()
    # wait for all threads to complete
    for t in threads:
        t.join()
    resultArray = ia(jobCount)
    for t in threads:
        qresult: JobResult = results.get()
        resultArray[qresult.id] = qresult.result
    return resultArray

def myFunc(index, param, results):
    # do your normal wokr here, params can be anything
    resultOfSomeWork = f'some result for param {param}'
    # the function needs to create a JobResult with the index and send it to the queue
    results.put(JobResult(index, resultOfSomeWork))

# an example calling a threading pool
def exampleCpuPool():
    params = [1, 2, 3]
    # my function to run in parallel
    resultsArray = ioPool(myFunc, params)
    for result in resultsArray:
        l(f'{result=}')
