import json
import requests

from flask import Flask, render_template, redirect, url_for, request, Response, abort, make_response, flash
from pymongo import Connection
from functools import wraps

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'this key is so secret'

DOGEPAY_API_KEY = '1b94bu21lq55xg1xct9z4trgnzc'
DOGEPAY_BASE_URL= 'https://www.dogeapi.com/wow/?api_key={0}&a='.format(DOGEPAY_API_KEY)
      
@app.route('/')
def show_home():
    return render_template('home.html')


# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
	app.debug=True
	app.run(host='0.0.0.0', processes=3)