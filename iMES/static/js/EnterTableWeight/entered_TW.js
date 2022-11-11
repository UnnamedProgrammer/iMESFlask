$(document).ready(function(){
    $('#productWeight').on('click', function(){
        entered_weight = document.getElementById('inputWeight').textContent;
        production_data = $('button').getAttribute('data-proddataoid');
        console.log(entered_weight)
        console.log(production_data)

        var socket = io();
        socket.emit('product_weight_entering', [entered_weight, production_data]);
    })
})