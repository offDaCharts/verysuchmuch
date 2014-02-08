import json
import requests

from flask import Flask, render_template, redirect, url_for, request, Response, abort, make_response, flash
from pymongo import Connection
from functools import wraps

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'this key is so secret'
      
      
@app.route('/')
def show_home():
    return render_template('home.html')


# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
	app.debug=True
	app.run(host='0.0.0.0', processes=3)