$(function(){
    //Success handler
    var successHandler = function(purchaseAction){
        console.log("Purchase completed successfully.");
    }

    //Failure handler
    var failureHandler = function(purchaseActionError){
        console.log("Purchase did not complete.");
    }

    function purchase(){
      google.payments.inapp.buy({
        'jwt'     : generatedJwt,
        'success' : successHandler,
        'failure' : failureHandler
      });
    }

});
