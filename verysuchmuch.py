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
    manualFloor = 1.5
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
            "exp" : int(time.time()) + 3600,
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

@app.route('/createOrder/<emailAddress>/<dogeAddress>/<dogeAmount>')
def createOrder(emailAddress, dogeAddress, dogeAmount):
    emailAddress = emailAddress.lower()
    ordersCollection = 'orders'
    purchasesCollection = 'purchases'
    dollarAmount = math.ceil(100 * float(get_dogeToDollarRate()) * float(dogeAmount)) / 100
    returnMessage = 'Success'

    if (db[ordersCollection].find({'email': emailAddress}).count() is not 0 or
     db[ordersCollection].find({'dogeAddress': dogeAddress}).count() is not 0):
        insertError = 'Existing Order'
        #Needs to display this error to user
        print "There already exists a current order with this email or doge address"
    else: 
        secondsInDay = 60 * 60 * 24
        result = db.purchases.aggregate([
            {'$match':{'email': emailAddress, 'time': {'$gt' : time.time() - secondsInDay}}}, 
            {'$group': {'_id': '$email', 'sum': {'$sum': '$dollarAmount'}}}
        ])['result']

        if len(result) is 0 or (result[0]['sum'] + dollarAmount) < 1000:
            minutesTilExpire = 30
            db[ordersCollection].insert({
                'email' : emailAddress,
                'dogeAddress' : dogeAddress,
                'dogeAmount' : float(dogeAmount),
                'dollarAmount' : dollarAmount,
                'dogeToDollarRate' : get_dogeToDollarRate(),
                'initTime' : int(time.time()),
                'expTime' : int(time.time()) + minutesTilExpire * 60
            })
            print 'Order Created'
        else:
            returnMessage = 'Limit Exceeded'
            #Need to display this error to user
            print "A single person cannot order more than $1000 in a 24 hour peroid"
    return returnMessage

def clearExpiredOrders():
    print "Checking for expired orders"
    collection = 'orders'
    cursor = db[collection].find()
    for doc in cursor:
        if time.time() > doc['expTime']:
            print "Removing expired order"
            db[collection].remove({'_id': doc['_id']})
    print "Expired orders checked and cleared\n"


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

@app.route('/get_dogeAPI_balance')
def get_dogeAPI_balance():
    return requests.get('{0}get_balance'.format(DOGEPAY_BASE_URL), verify=False).text.replace('"', '')

@app.route('/get_current_balance')
def get_balance():
    balance = float(get_dogeAPI_balance())
    ordersResult = db.orders.aggregate([{'$group': {'_id': '', 'sum': {'$sum': '$dogeAmount'}}}])['result']
    if len(ordersResult) > 0:
        balance = balance - float(ordersResult[0]['sum'])

    #Subtract purchases in last 10min incase doge api hasn't updated with most recent purchases
    purchasesResult = db.purchases.aggregate([
        {'$match':{'time': {'$gt' : time.time() - 10*60}}}, 
        {'$group': {'_id': '', 'sum': {'$sum': '$dogeAmount'}}}
    ])['result']
    if len(purchasesResult) > 0:
        balance = balance - float(purchasesResult[0]['sum'])

    return str(balance)

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
    ordersCollection = 'orders'
    purchasesCollection = 'purchases'

    validFlag = True
    header = re.match(r'^(((?!Subject)[^$])*)(Subject)', message).group()
    body = message[len(header):]
    if not "wallet.google" in header:
        validFlag = False

    bodyMatch = re.match(r'([^$]*)(\$)([\d,.]+)([^<]*<)([^>]*)', body)
    if bodyMatch is None:
        validFlag = False
    else:
        dollarAmount = float(bodyMatch.group(3))
        email = bodyMatch.group(5).lower()
        print dollarAmount, email
        if db[ordersCollection].find({'email': email}).count() is 0:
            print "Payment sent from email with no open orders"
            validFlag = False

    if validFlag:
        orderDoc = db[ordersCollection].find({'email': email})[0]

        if dollarAmount >= float(orderDoc['dollarAmount']):
            #If they try to buy more than ordered, they will only get sent the amount they ordered
            dollarAmount = float(orderDoc['dollarAmount'])
            dogeAmount = int(orderDoc['dogeAmount'])
        else:
            #If they send less than what they ordered, then they will be given what they pay for
            dogeAmount = int(math.floor(dollarAmount/float(get_dogeToDollarRate())))

        dogeAddress = orderDoc['dogeAddress']
        db[ordersCollection].remove({'_id': orderDoc['_id']})
        db[purchasesCollection].insert({
            'email' : email,
            'dogeAddress' : dogeAddress,
            'dollarAmount' : dollarAmount,
            'dogeAmount' : dogeAmount,
            'time' : time.time()
        })

        print str(dogeAmount)
        print dogeAddress
        #print "doge would be sent here if not testing"
        print "sending"
        send_doge(dogeAmount, dogeAddress)

def check_mail():
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
    print "Consider your mail checked\n"
    return "Done"

def mail_cron_job():
    #Runs every half minute
    secondsWait = 30
    Timer(secondsWait, mail_cron_job, ()).start()
    check_mail()
    clearExpiredOrders()

mail_cron_job()

# App Configuration
# This section holds all application specific configuration options.

if __name__ == '__main__':
    app.debug=True
    #use_reloader is set to false so mail cron job is only called once
    app.run(host='0.0.0.0', port=5555,  processes=3, use_reloader=False)