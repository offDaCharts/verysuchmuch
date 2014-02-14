import json
import requests
import jwt
import time
import os
import math
import re

from flask import Flask, render_template, redirect, url_for, request, Response, abort, make_response, flash
from pymongo import Connection
from functools import wraps

app = Flask(__name__)
app.config.from_object(__name__)

app.config.from_object('sellerinfo')
app.secret_key = 'this key is so secret'

DOGEPAY_API_KEY = '1b94bu21lq55xg1xct9z4trgnzc'
DOGEPAY_BASE_URL= 'https://www.dogeapi.com/wow/?api_key={0}&a='.format(DOGEPAY_API_KEY)

connection = Connection()
db = connection['verysuchmuch']
      
@app.route('/')
def show_home():
    return render_template('home.html')

@app.route('/about')
def show_about():
    return render_template('about.html')

@app.route('/dogeToDollarRate')
def get_dogeToDollarRate():
    manualFloor = 2.6
    marketMarkup = math.ceil(float(get_doge_pay_price()) * 1.3 * 100) / 100
    rate = marketMarkup if marketMarkup > manualFloor else manualFloor
    return str(rate / 1000)

@app.route('/jwt/<dogeAmount>/<dogeAddress>')
def getJWT(dogeAmount, dogeAddress):
    rate = float(get_dogeToDollarRate())
    dollarAmount = math.ceil(100 * (float(dogeAmount) * rate)) / 100
    return jwt.encode(
        {
            "iss" : app.config['SELLER_ID'],
            "aud" : "Google",
            "typ" : "google/payments/inapp/item/v1",
            "exp" : int(time.time() + 3600),
            "iat" : int(time.time()),
            "request" :{
              "name" : str(dogeAmount) + "Doge",
              "description" : "Currency out of this World!",
              "price" : str(dollarAmount),
              "currencyCode" : "USD",
              "sellerData": "{0}_{1}".format(dogeAddress,dogeAmount)
            }
        },
        app.config['SELLER_SECRET'])

@app.route('/success_jwt', methods=["POST"])
def successful_purchase():
    response_jwt = jwt.decode(request.form['jwt'], app.config['SELLER_SECRET'])
    dogeAddress, dogeAmount = response_jwt['request']['sellerData'].split("_")
    dogeAmount = float(dogeAmount)
    if send_doge(amount=dogeAmount,address=dogeAddress):
        db['transactions'].insert({
                                   'time' : response_jwt['iat'],
                                   'dollarAmount' : response_jwt['request']['price'],
                                   'dogeAmount' : dogeAmount,
                                   'dogeAddress': dogeAddress,
                                   'googleOrderID' : response_jwt['response']['orderId']
                                   })
        resp = make_response(json.dumps(response_jwt['response']['orderId']), 200)
        resp.headers.extend({})
        return resp
    else:
        resp = make_response(json.dumps("No Transaction Executed."), 501)
        resp.headers.extend({})
        return resp
        
#Dogepay Route

@app.route('/get_doge_pay_price')
def get_doge_pay_price():
    responseHtml = requests.get('http://www.dogepay.com', verify=False).text
    responseHtml = re.sub('[<>\n"\']', '', responseHtml)
    try:
        pricePerMegaDoge = re.match(r'[^$]*\d[^L]*(Last Value)([^$]*)(\$)([\d,.]+)', responseHtml).group(4).replace(',','')
        rate = str(float(pricePerMegaDoge)/1000)
    except:
        rate = get_market_dogeToDollarRate()
    return rate
    


# DogeAPI Routes

@app.route('/get_current_balance')
def get_balance():
    return requests.get('{0}get_balance'.format(DOGEPAY_BASE_URL), verify=False).text

def get_market_dogeToDollarRate():
    return requests.get('{0}get_current_price&amount_doge=1000'.format(DOGEPAY_BASE_URL), verify=False).text

def send_doge(amount=None, address=None):
    print amount, address
    if address == None or amount == None or amount < 5:
        return False
    amount = (amount/.995)
    dogeAPIResponse = requests.get('{0}withdraw&amount={1}&payment_address={2}'.format(DOGEPAY_BASE_URL, amount, address)).text
    if len(dogeAPIResponse):
        return True
    return False
# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
	app.debug=True
	app.run(host='0.0.0.0', port=5555,  processes=3)
