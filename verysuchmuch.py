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

@app.route('/about')
def show_about():
    return render_template('about.html')


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
              "currencyCode" : "USD"
            }
        },
        app.config['SELLER_SECRET'])

@app.route('/purchase_success', methods=["POST"])
def successful_purchase():
    response_jwt = jwt.decode(request.form['jwt'], app.config['SELLER_SECRET'])
    print response_jwt
    resp = make_response(json.dumps(response_jwt['response']['orderId']), 200)
    resp.headers.extend({})
    return resp
    return 201

# DogeAPI Routes

@app.route('/get_current_balance')
def get_balance():
    return requests.get('{0}get_balance'.format(DOGEPAY_BASE_URL)).text

def send_doge(amount=None, address=None):
    print amount, address
    if address == None or amount == None or amount < 5:
        return 'Invalid Payment Parameters'
    amount = (amount/.995)
    return requests.get('{0}withdraw&amount={1}&payment_address={2}'.format(DOGEPAY_BASE_URL, amount, address)).text

# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
	app.debug=True
	app.run(host='0.0.0.0', port=5555,  processes=3)
