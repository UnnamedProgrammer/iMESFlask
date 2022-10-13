$(document).ready(function(){
    $('#weightEntering').click(function(){
        entered_weight = document.getElementById('inputWeight').textContent;

        var socket = io();
        socket.emit('product_weight_entering', entered_weight);
    })
    $('#printWeight').click(function(){
        var socket = io();
        socket.emit('product_weight_printing');
    })
})