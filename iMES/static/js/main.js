let tpaOid = document.getElementById('ttpa').dataset.oid // Oid текущего ТПА 
let pressForm = document.getElementById('tpf') // Текущая пресс-форма
let current_user = document.getElementById('current_user').value.replace(/[^a-zа-яё\s]/gi, '').replace('User', ''); // Текущий пользователь

function changeTPA(event){
    let tpaOid = event.target.dataset.oid;
    let tpaName = event.target.dataset.name;

    xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
        if (xhr.readyState == 4 && xhr.status == 200) {
            location.reload()
        }
    }
    xhr.open("GET", "/changeTpa?oid="+tpaOid+"&name="+tpaName, true)
    xhr.send()
}

// Управдление панелями
function offcanvasControl(event) {
    offcanvasPanel = document.querySelectorAll('.offcanvas')

    for ( let i = 0; i <= offcanvasPanel.length; i++) {
        if(offcanvasPanel[i].id == event.target.id) {
            offcanvasPanel[i] = !offcanvasPanel[i].classList.contains('show') ? offcanvasPanel[i].classList.add('show') : offcanvasPanel[i].classList.remove('show')
        }
        if ( i <= offcanvasPanel.length) break
    }
    
}

// Управление модальным окном
function modalController(event){ 
    toggler = event.target.dataset.toggle // Кнопка открытия/закрытия модального окна
    target = event.target.dataset.target // ID модального окна ( атрибут data-target )
    modal = document.getElementById(target) // Получение нужного модальног окна по ID
    // Открытие/закрытие модального окна
    modal.classList.toggle('hidden');
}

// Печать этикетки
function stickerPrint() {

    mywindow = window.open('', 'PRINT', 'height=400,width=600,left=300,top=300');

    let tprod = document.getElementById('tprod').innerHTML,
        smena = document.getElementById('smena').innerHTML,
        nvplan = document.getElementById('nvplan').innerHTML,
        operator = document.getElementById('operator').innerHTML,
        clock = document.getElementById('clock').innerHTML,

    html ="";

    html += '<div>----------------------------------</div>'
    +'<b>Артикул</b> '+tprod+'<br>'
    +'<b>Дата</b> '+ clock +' <br>'
    +'<b>Смена</b> '+ smena +'<br>'
    +'<b>Количество</b> '+ nvplan +'<br>'
    +'<b>Упаковщик</b> '+ operator +'<br>';
    var div = '<div class="my_print">'+html+'<div>----------------------------------</div></div>';

    printStickerWindow(div, mywindow);
}

// Печать итогов за смену
function stickerPrintTotal() {

    mywindow = window.open('', 'PRINT', 'height=400,width=600,left=300,top=300');

    let tpa = document.getElementById('ttpa').innerHTML,
        tprod = document.getElementById('tprod').innerHTML,
        smena = document.getElementById('smena').innerHTML,
        nvplan = document.getElementById('nvplan').innerHTML,
        operator = document.getElementById('operator').innerHTML,
        clock = document.getElementById('clock').innerHTML,

    html ="";
    
    html += '<div>----------------------------------</div>'
    +smena+'<br>'
    +tpa+ '<br>'
    +'План на смену: <br>'
    +'Оператор: '+'<br>'
    +'Наладчик: '+'<br>'
    +'Простои: '+'<br>'
    var div = '<div class="my_print">'+html+'<div>----------------------------------</div></div>';

    printStickerWindow(div, mywindow);
}

// Окно печати
function printStickerWindow(elem, mywindow){  
    mywindow.document.write(elem);
    var printerPaper = document.querySelector('#printerPaper');
    if(printerPaper){
        var px =  mywindow.document.body.querySelector('div').offsetHeight;
        printerPaper.setAttribute('data', px);
    }

    mywindow.document.close();
    mywindow.focus();
    mywindow.print();
    mywindow.close(); 
    // minusPaper();
}