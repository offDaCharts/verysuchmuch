$(function() {
    $.get("/dogeToDollarRate", function (dogeToDollarRate) {
        var dollarToDogeRate = 1/dogeToDollarRate;
            //Success handler
            successHandler = function(purchaseAction){
                $.post("/success_jwt", {'jwt': purchaseAction.jwt}, function (data) {
                   //Here we'll tell the user to check their doge wallet for the Doge! 
                });
            },
            //Failure handler
            failureHandler = function(purchaseActionError){
                alert("So... Something went wrong. The payment has been canceled and you won't be charged. If the problem persists, email us at support@verysuchmuch.com")
                console.log("Purchase did not complete.", purchaseActionError);
            },
            purchase = function(dogeAmount, dogeAddress){
                $.get("/jwt/" + dogeAmount + "/" + dogeAddress,
                    function(generatedJwt) {
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

        $("#dollarAmount").attr("placeholder", "Price: " + dogeToDollarRate*1000 + "$/1kDoge"); 

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
                dollarRoundedUpCent = Math.ceil(+$("#dollarAmount").val()*100)/100,
                dogeWallet = $("#dogeWallet").val();

            $("#dogeAmount").val(flooredDoge);
            $("#dollarAmount").val(dollarRoundedUpCent);

            if(validate() && dogeWallet.length) {
                $.get("/get_current_balance",
                    function(balance) {
                        balance = balance.replace(/\"/g, "");
                        if (+balance >= +flooredDoge) {
                            purchase(flooredDoge, dogeWallet);
                        } else {
                            $("#errorMessage").show();                
                            $("#errorMessage").text("Sorry, we currently only have " + Math.floor(balance) +
                                "Doge left. We will restock soon.");                
                        }
                });
            } else {
                $("#errorMessage").show();                
                $("#errorMessage").text("Please enter a Doge Address");                
            }
        });
    });
});