#!/usr/bin/env python

import os
import imp
import datetime
import logging
import socket
import flask.ext

from flask import Flask, jsonify, request
from multiprocessing import Process, Queue
import prometheus_client as prom

# mod = imp.load_source('function',
#                       '/kubeless/%s.py' % os.getenv('MOD_NAME', 'test'))
func = 'hellox' #getattr(mod, os.getenv('FUNC_HANDLER'))
func_port = os.getenv('FUNC_PORT', 8080)

timeout = float(os.getenv('FUNC_TIMEOUT', 180))

log = logging.getLogger(__name__)
app = Flask(__name__)

func_hist = prom.Histogram('function_duration_seconds',
                           'Duration of user function in seconds',
                           ['method'])
func_calls = prom.Counter('function_calls_total',
                           'Number of calls to user function',
                          ['method'])
func_errors = prom.Counter('function_failures_total',
                           'Number of exceptions in user function',
                           ['method'])

function_context = {
    'function-name': func,
    'timeout': timeout,
    'runtime': os.getenv('FUNC_RUNTIME'),
    'memory-limit': os.getenv('FUNC_MEMORY_LIMIT'),
}

def funcWrap(q, event, c):
    try:
        q.put(func(event, c))
    except Exception as inst:
        q.put(inst)

@app.route('/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def handler():
    req = request
    req.get_data()
    content_type = req.headers.get('content-type')
    data = req.data
    if content_type == 'application/json':
        data = req.json
    event = {
        'data': data,
        'event-id': req.headers.get('event-id'),
        'event-type': req.headers.get('event-type'),
        'event-time': req.headers.get('event-time'),
        'event-namespace': req.headers.get('event-namespace'),
        'extensions': {
            'request': req
        }
    }
    method = req.method
    func_calls.labels(method).inc()
    with func_errors.labels(method).count_exceptions():
        with func_hist.labels(method).time():
            q = Queue()
            p = Process(target=funcWrap, args=(q, event, function_context))
            p.start()
            p.join(timeout)
            # If thread is still active
            if p.is_alive():
                p.terminate()
                p.join()
                return "Timeout while processing the function", 408
            else:
                res = q.get()
                if isinstance(res, Exception):
                    raise res
                return res

@app.route('/healthz', methods=['GET'])
def healthz():
    return 'OK', 200

@app.route('/metrics', methods=['GET'])
def metrics():
    # bottle.response.content_type = prom.CONTENT_TYPE_LATEST
    app.response.headers["Content-Type"] = prom.CONTENT_TYPE_LATEST
    return prom.generate_latest(prom.REGISTRY)

if __name__ == '__main__':
    import logging
    import sys
    import requestlogger
    loggedapp = requestlogger.WSGILogger(
        app,
        [logging.StreamHandler(stream=sys.stdout)],
        requestlogger.ApacheFormatter())
    app.run(host='0.0.0.0', port=func_port)

