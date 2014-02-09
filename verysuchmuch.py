import json
import requests
import jwt
import time
import os

from flask import Flask, render_template, redirect, url_for, request, Response, abort, make_response, flash
from pymongo import Connection
from functools import wraps

app = Flask(__name__)
app.config.from_object(__name__)

app.config.from_object('sellerinfo')
app.secret_key = 'this key is so secret'

DOGEPAY_API_KEY = '1b94bu21lq55xg1xct9z4trgnzc'
DOGEPAY_BASE_URL= 'https://www.dogeapi.com/wow/?api_key={0}&a='.format(DOGEPAY_API_KEY)
      
@app.route('/')
def show_home():
    return render_template('home.html')

@app.route('/payment')
def show_testPayment():
    return render_template('testPaymentAPI.html')


@app.route('/jwt/<dollarAmount>', methods=["GET"])
def getJWT(dollarAmount):
    return jwt.encode(
        {
            "iss" : app.config['SELLER_ID'],
            "aud" : "Google",
            "typ" : "google/payments/inapp/item/v1",
            "exp" : int(time.time() + 3600),
            "iat" : int(time.time()),
            "request" :{
              "name" : "Piece of Cake",
              "description" : "Virtual chocolate cake to fill your virtual tummy",
              "price" : str(dollarAmount),
              "currencyCode" : "USD",
              "sellerData" : "user_id:1224245,offer_code:3098576987,affiliate:aksdfbovu9j"
            }
        },
        app.config['SELLER_SECRET'])

# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
	app.debug=True
	app.run(host='0.0.0.0', processes=3)