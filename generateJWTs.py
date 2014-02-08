cakeToken = jwt.encode(
  {
    "iss" : sellerIdentifier,
    "aud" : "Google",
    "typ" : "google/payments/inapp/item/v1",
    "exp" : int(time.time() + 3600),
    "iat" : int(time.time()),
    "request" :{
      "name" : "Piece of Cake",
      "description" : "Virtual chocolate cake to fill your virtual tummy",
      "price" : "10.50",
      "currencyCode" : "USD",
      "sellerData" : "user_id:1224245,offer_code:3098576987,affiliate:aksdfbovu9j"
    }
  },
  SELLER_SECRET)