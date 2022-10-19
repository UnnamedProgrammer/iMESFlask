$(document).ready(function(){
    $('[data-selectproduct]').click(function(){
        entered_weight = document.getElementById('productWeightData').textContent;
        production_data = $(this).attr('data-productiondata');
        
        var socket = io();
        socket.emit('product_weight_entering', [entered_weight, production_data]);
    })
})