$(function(){
    //Success handler
    var successHandler = function(purchaseAction){
            console.log("Purchase completed successfully.");
        },
        //Failure handler
        failureHandler = function(purchaseActionError){
            console.log("Purchase did not complete.");
        },

        purchase = function(){
            console.log("purchasing");
            $.get("/jwt",
                function(generatedJwt) {
                    console.log(generatedJwt);
                    google.payments.inapp.buy({
                        'jwt'     : generatedJwt,
                        'success' : successHandler,
                        'failure' : failureHandler
                    });
                }
            );
        };

    $("#buybutton1").click(purchase);
});
