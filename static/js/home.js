$(function() {
    var dogeToDollarRate = 1.5/1000,
        dollarToDogeRate = 1/dogeToDollarRate;
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

});