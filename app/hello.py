""" hello.py """

import logging
import socket

from flask import Flask, jsonify, request

log = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        'hello': 'world',
        'host': socket.gethostname()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9875)
