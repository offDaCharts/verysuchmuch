$(function() {
    var dogeToDollarRate = 1.5/1000,
        dollarToDogeRate = 1/dogeToDollarRate;
        //Success handler
        successHandler = function(purchaseAction){
            console.log("Purchase completed successfully.");
        },
        //Failure handler
        failureHandler = function(purchaseActionError){
            console.log("Purchase did not complete.", purchaseActionError);
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
        },
        validate = function() {
            if (isNaN(+$("#dogeAmount").val()) || isNaN(+$("#dollarAmount").val())) {
                $("#errorMessage").show();                
                $("#errorMessage").text("Must enter a number");
                return 0;
            } else if(+$("#dogeAmount").val() < 5) {
                $("#errorMessage").show();                
                $("#errorMessage").text("Must be 5 or more Doge");
                return 0; 
            } else if ($("#dogeWallet").val().length && !$("#dogeWallet").val().match(/^D[A-Z0-9][A-Za-z0-9]{30,32}$/)) {
                $("#errorMessage").show();                
                $("#errorMessage").text("Invalid Doge Address");                
                return 0;
            } else {
                $("#errorMessage").hide();                
                return 1;
            }
        };

    $("#errorMessage").hide();                

    $("#dogeAmount").keyup(function() {
        if (isNaN(+$(this).val())) {
            $("#dollarAmount").val("");
        } else {
            $("#dollarAmount").val(+$(this).val()*dogeToDollarRate);
        }
        validate();
    });

    $("#dollarAmount").keyup(function() {
        if (isNaN(+$(this).val())) {
            $("#dogeAmount").val("");
        } else {
            $("#dogeAmount").val(Math.floor(+$(this).val()*dollarToDogeRate));
        }
        validate();
    });

    $("#dogeWallet").keyup(function() {
        validate();
    });

    $("#purchaseButton").click(function(e) {
        e.preventDefault();
        if (isNaN(+$("#dollarAmount").val())) {
            $("#dogeAmount").val("");
        } else {
            $("#dogeAmount").val(Math.floor(+$("#dollarAmount").val()*dollarToDogeRate));
        }

        var flooredDoge = Math.floor(+$("#dogeAmount").val()),
            dollarRoundedUpCent = Math.ceil(+$("#dollarAmount").val()*100)/100;

        $("#dogeAmount").val(flooredDoge);
        $("#dollarAmount").val(dollarRoundedUpCent);

        if(validate()) {
            purchase(dollarRoundedUpCent);
        }
    });



});