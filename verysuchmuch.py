import json
import requests
import jwt
import time
import os
import math
import re
import imaplib
import time

from flask import Flask, render_template, redirect, url_for, request, Response, abort, make_response, flash
from pymongo import Connection
from functools import wraps
from threading import Timer

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

@app.route('/thankyou')
def show_thankyou():
    return render_template('thankyou.html')

@app.route('/about')
def show_about():
    return render_template('about.html')

@app.route('/dogeToDollarRate')
def get_dogeToDollarRate():
    manualFloor = 1.87
    percentMarkup = 35
    marketMarkup = math.ceil(float(get_doge_pay_price()) * (1 + float(percentMarkup)/100) * 100) / 100
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
              "name" : str(dogeAmount) + " Doge",
              "description" : "Tickets to the Moon!",
              "price" : str(dollarAmount),
              "currencyCode" : "USD",
              "sellerData": "{0}_{1}".format(dogeAddress,dogeAmount)
            }
        },
        app.config['SELLER_SECRET'])

@app.route('/emailAndWallet/<emailAddress>/<dogeAddress>')
def addEmailandWalletPair(emailAddress, dogeAddress):
    collection = 'emailAndWallet'
    insertSuccess = True
    print emailAddress
    print dogeAddress
    if (db[collection].find({'email': emailAddress.lower()}).count() is not 0 or
     db[collection].find({'dogeAddress': dogeAddress}).count() is not 0):
        insertSuccess = False
        print "There already exists a current order with this email or doge address"
        print "Please complete your order or wait 30min to cancel"
    else: 
        db[collection].insert({
            'email' : emailAddress,
            'dogeAddress' : dogeAddress,
            'initTime' : int(time.time()),
            'expTime' : int(time.time() + 3600)
        })
    return str(insertSuccess)

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
    #dogeAPIResponse = requests.get('{0}withdraw&amount={1}&payment_address={2}'.format(DOGEPAY_BASE_URL, amount, address)).text
    dogeAPIResponse = requests.get('{0}withdraw&amount={1}&payment_address={2}'.format(DOGEPAY_BASE_URL, amount, address), verify=False).text
    if len(dogeAPIResponse):
        return True
    return False


# Mail Routes

def parse_email(message):
    collection = 'emailAndWallet'
    validFlag = True
    header = re.match(r'^(((?!Subject)[^$])*)(Subject)', message).group()
    body = message[len(header):]
    if not "wallet.google" in header:
        validFlag = False

    bodyMatch = re.match(r'([^$]*)(\$)([\d,.]+)([^<]*<)([^>]*)', body)
    if bodyMatch is None:
        validFlag = False
    else:
        amount = bodyMatch.group(3)
        email = bodyMatch.group(5).lower()
        print amount
        print email
        if db[collection].find({'email': email}).count() is 0:
            print "Payment sent from email with no open orders"
            validFlag = False            

    if validFlag:
        amount = float(amount)
        dogeAmount = int(math.floor(amount/float(get_dogeToDollarRate())))

        
        emailAndWalletDoc = db[collection].find({'email': email})[0]
        dogeAddress = emailAndWalletDoc['dogeAddress']
        db[collection].remove({'_id': emailAndWalletDoc['_id']})

        print str(dogeAmount)
        print dogeAddress
        print "doge would be sent here if not testing"
        #print "sending"
        #send_doge(dogeAmount, dogeAddress)

def get_mail():
    print "Checking mail"
    mail = imaplib.IMAP4_SSL('imap.gmail.com', '993')
    mail.login('verysuchmuch', app.config['EMAIL_PASSWORD'])
    mail.select('wallet')

    typ, data = mail.search(None, 'UNSEEN')
    for num in data[0].split():
        typ, data = mail.fetch(num, '(RFC822)')
        message = 'Message %s\n%s\n' % (num, data[0][1])
        parse_email(message)

    mail.close()
    mail.logout()
    print "Consider your mail checked"
    return "done"

def mail_cron_job():
    secondsWait = 60
    get_mail()
    Timer(secondsWait, mail_cron_job, ()).start()

mail_cron_job()

# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
    app.debug=True
    #use_reloader is set to false so mail cron job is only called once
    app.run(host='0.0.0.0', port=5555,  processes=3, use_reloader=False)