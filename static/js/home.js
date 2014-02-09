$(function() {
    var dogeToDollarRate = 1.5/1000,
        dollarToDogeRate = 1/dogeToDollarRate;
        //Success handler
        successHandler = function(purchaseAction){
            console.log("Purchase completed successfully.");
        },
        //Failure handler
        failureHandler = function(purchaseActionError){
            console.log("Purchase did not complete.");
        },
        purchase = function(dollarAmount){
            console.log("purchasing");
            $.get("/jwt/" + dollarAmount,
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

    $("#dogeAmount").keyup(function() {
        if (isNaN(+$(this).val())) {
            $("#dollarAmount").val("");
        } else {
            $("#dollarAmount").val(+$(this).val()*dogeToDollarRate);
        }
    });

    $("#dollarAmount").keyup(function() {
        if (isNaN(+$(this).val())) {
            $("#dogeAmount").val("");
        } else {
            $("#dogeAmount").val(Math.floor(+$(this).val()*dollarToDogeRate));
        }
    });

    $("#purchaseButton").click(function(e) {
        e.preventDefault();
        var flooredDoge = Math.floor(+$("#dogeAmount").val()),
            dollarRoundedUpCent = Math.ceil(+$("#dollarAmount").val()*100)/100;
        $("#dogeAmount").val(flooredDoge);
        $("#dollarAmount").val(dollarRoundedUpCent);
        purchase(dollarRoundedUpCent);
    });



});