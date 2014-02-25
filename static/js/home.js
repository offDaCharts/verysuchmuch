$(function() {
    $.get("/dogeToDollarRate", function (dogeToDollarRate) {
        var dollarToDogeRate = 1/dogeToDollarRate;
            //Success handler
            successHandler = function(purchaseAction) {
                $.post("/success_jwt", {'jwt': purchaseAction.jwt}, function (data) {
                   //Here we'll tell the user to check their doge wallet for the Doge!
                    document.location.href = '/thankyou';
                });
            },
            //Failure handler
            failureHandler = function(purchaseActionError) {
                alert("So... Something went wrong. The payment has been canceled and you won't be charged. If the problem persists, email us at support@verysuchmuch.com");
                console.log("Purchase did not complete.", purchaseActionError);
            },
            createOrder = function(emailAddress, dogeAddress, dogeAmount) {
                $.get("/createOrder/" + emailAddress + "/" + dogeAddress + "/" + dogeAmount,
                    function(message) {
                        if (message === "Existing Order") {
                            //pre existing order exists
                            $("#modalErrorMessage")
                                .text("There already exists an order with this email or Doge address" +
                                    "Please complete that order or wait 30minutes to cancel")
                                .show();
                        } else if (message === "Limit Exceeded") {
                            console.log(1);
                            //1000$/day limit
                            $("#modalErrorMessage")
                                .text("You are not allowed to buy more than $1000 in a 24hour peroid")
                                .show();
                        } else {
                            //Order Placed
                            $("#modalErrorMessage")
                                .removeClass("alert-danger")
                                .addClass("alert-success")
                                .text("Order Placed")
                                .show();
                        }
                    }
                );
            },
            showCreateOrderModal = function(dogeAmount, dogeWallet, dollarAmount) {
                $("#modalDogeAmount").text(dogeAmount);
                $("#modalDogeAddress").text(dogeWallet);
                $("#modalDollarAmount").text(dollarAmount);
                $("#createOrderButton").unbind();
                $("#createOrderButton").click(function() {
                    createOrder($("#email").val(), dogeWallet, dogeAmount);
                });
                $(".create-order").modal("show");
            },
            purchase = function(dogeAmount, dogeAddress) {
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

            //var flooredDoge = Math.floor(+$("#dogeAmount").val()),
            var flooredDoge = Math.round(+$("#dogeAmount").val()),
                dollarRoundedUpCent = Math.ceil(+$("#dollarAmount").val()*100)/100,
                dogeWallet = $("#dogeWallet").val();

            $("#dogeAmount").val(flooredDoge);
            $("#dollarAmount").val(dollarRoundedUpCent);

            if(validate() && dogeWallet.length) {
                $.get("/get_current_balance",
                    function(balance) {
                        balance = +balance * 0.995;
                        if (+balance >= +flooredDoge) {
                            showCreateOrderModal(flooredDoge, dogeWallet, dollarRoundedUpCent);

                            //The old way with google merchant
                            //purchase(flooredDoge, dogeWallet);
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
        $.get("/get_current_balance", 
            function(balance){
                if (balance < 1000) {
                    $(".sold-out").modal('show');
                    $("#purchaseButton").prop('disabled', true);
                }
        });
        
        $.get("/get_doge_sold", //Here we display how much doge we've sold!
            function(dogeSold) {
                $('#dogeSold').toggleClass("hidden");
                $('.odometer').text(dogeSold);        
        });
    });
});