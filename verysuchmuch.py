import json
import requests
import jwt
import time
import os
import math
import re

import imaplib

# import urllib2
# import poplib
# from email import parser

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

@app.route('/get_mail')
def get_mail():
    mail = imaplib.IMAP4_SSL('imap.gmail.com', '993')
    mail.login('verysuchmuch', app.config['EMAIL_PASSWORD'])
    mail.select('wallet')

    typ, data = mail.search(None, 'UNSEEN')
    for num in data[0].split():
        validFlag = True
        typ, data = mail.fetch(num, '(RFC822)')
        message = 'Message %s\n%s\n' % (num, data[0][1])
        #match = re.match(r'google\.com: domain of noreply@wallet\.google\.com designates [^\s]* as permitted sender', message)
        header = re.match(r'^(((?!Subject)[^$])*)(Subject)', message).group()
        body = message[len(header):]
        print "here"
        if not "wallet.google" in header:
            print "false"
            validFlag = False

        bodyMatch = re.match(r'([^$]*)(\$)([\d,.]+)([^<]*<)([^>]*)', body)
        if bodyMatch is None:
            print "false"
            validFlag = False
        else:
            amount = bodyMatch.group(3)
            email = bodyMatch.group(5)
            print amount
            print email

        if validFlag:
            #send doge
            print amount
            amount = float(amount)
            dogeAmount = int(math.floor(amount/float(get_dogeToDollarRate())))
            print str(dogeAmount)

            #TODO need to have people give email and address to create email to address hash in db
            quinsDogeWallet = "DFXrRgnxyVhxYry234ctDoGwVXXgBUKGYM"

            #print "sending"
            #send_doge(dogeAmount, quinsDogeWallet)

    mail.close()
    mail.logout()
    print "done"
    return body

#other tries
# @app.route('/get_gmail_inbox_feed')
# def get_gmail_inbox_feed():
#     # create a password manager
#     password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

#     # Add the username and password.
#     # If we knew the realm, we could use it instead of None.
#     top_level_url = "https://mail.google.com/mail/feed/atom/wallet"
#     password = "*******"
#     password_mgr.add_password(None, top_level_url, "robqthames@gmail.com", password)

#     handler = urllib2.HTTPBasicAuthHandler(password_mgr)

#     # create "opener" (OpenerDirector instance)
#     opener = urllib2.build_opener(handler)

#     # use the opener to fetch a URL
#     test = opener.open(top_level_url)
#     print test

#     # Install the opener.
#     # Now all calls to urllib2.urlopen use our opener.
#     urllib2.install_opener(opener)

#     req = urllib2.Request(top_level_url)
#     response = urllib2.urlopen(req)
#     the_page = response.read()
#     return the_page

# @app.route('/get_gmail_over_pop')
# def get_gmail_over_pop():
#     pop_conn = poplib.POP3_SSL('pop.gmail.com')
#     pop_conn.user('verysuchmuch@gmail.com')
#     pop_conn.pass_('*************')

#     print "connecting"
#     #Get messages from server:
#     messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
#     # Concat message pieces:
#     messages = ["\n".join(mssg[1]) for mssg in messages]
#     #Parse message intom an email object:
#     messages = [parser.Parser().parsestr(mssg) for mssg in messages]
#     for message in messages:
#         print message['subject']
#     pop_conn.quit()
#     return "testing"



# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
	app.debug=True
	app.run(host='0.0.0.0', port=5555,  processes=3)
