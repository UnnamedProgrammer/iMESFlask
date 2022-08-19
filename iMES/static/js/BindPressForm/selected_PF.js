$(document).ready(function(){
    // Записываю value в переменную selected_press_form выбранного option
    $('#selectPressForm').change(function () {
        selected_press_form = document.getElementById('selectPressForm').value;
        // Название выбранной пресс-формы, если когда-нибудь пригодиться 
        // selected_press_form_txt = $( "#selectPressForm option:selected" ).text();    
    });
    // При нажатии на кнопку отправляю идентификаторы контроллера и выбранной пресс-формы на сервер
    $('#bindPressForm').click(function(){
        var socket = io();
        socket.emit('press_form_binding', [selected_press_form, document.getElementById('conOid').value]);
    })
})
