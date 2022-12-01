let tpaOid = document.getElementById('ttpa').dataset.oid // Oid текущего ТПА 
let pressForm = document.getElementById('tpf') // Текущая пресс-форма
let current_user = document.getElementById('current_user').value.replace(/[^a-zа-яё\s]/gi, '').replace('User', ''); // Текущий пользователь

let ttpa = document.getElementById('ttpa').innerHTML,
    tprod = document.getElementById('tprod').innerHTML,
    smena = document.getElementById('smena').innerHTML,
    nvplan = document.getElementById('nvplan').innerHTML,
    operator = document.getElementById('operator').innerHTML,
    clock = document.getElementById('clock').innerHTML

let showMoreButton = document.querySelectorAll('.show-more')
    closeMoreButton = document.querySelectorAll('.close-more')

setTimeout(function(){
    ttpa = document.getElementById('ttpa').innerHTML,
    tprod = document.getElementById('tprod').innerHTML,
    smena = document.getElementById('smena').innerHTML,
    nvplan = document.getElementById('nvplan').innerHTML,
    operator = document.getElementById('operator').innerHTML,
    clock = document.getElementById('clock').innerHTML;
},500);

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

// Управдление панелями}
$("#tpaPanelButton").click(function() {
    $('.offcanvas').addClass('show');
    $('.offcanvas-blur').removeClass('hidden');
  });

$(document).mouseup(function (e) {
    var container = $(".offcanvas");
    if (container.has(e.target).length === 0){
        container.removeClass('show');
        $('.offcanvas-blur').addClass('hidden');
    }
});

// Управление модальным окном
function modalController(event){ 
    toggler = event.target.dataset.toggle // Кнопка открытия/закрытия модального окна
    target = event.target.dataset.target // ID модального окна ( атрибут data-target )
    modal = document.getElementById(target) // Получение нужного модальног окна по ID
    // Открытие/закрытие модального окна
    modal.classList.toggle('hidden');
}

function commentModalController(event) {
    Keyboard.open()
    target = event.target.dataset.target
    modal = document.getElementById(target)
    modal.classList.toggle('hidden')
    commentInput = document.getElementById('commentInput')
    commentInput.focus()
    commentInput.dataset.data = event.target.dataset.wasteoid
}

// Печать этикетки
function stickerPrint() {

    mywindow = window.open('', 'PRINT', 'height=400,width=600,left=300,top=300');

    let clock = document.getElementById('clock').innerHTML,
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

    let clock = document.getElementById('clock').innerHTML,
        html ="";
    
    html += '<div>----------------------------------</div>'
    +smena+'<br>'
    +ttpa+ '<br>'
    +'План на смену: <br>'
    +'Оператор: '+'<br>'
    +'Наладчик: '+'<br>'
    +'Простои: '+'<br>'
    let div = '<div class="my_print">'+html+'<div>----------------------------------</div></div>'; 

    printStickerWindow(div, mywindow);
}

// Окно печати
function printStickerWindow(elem, mywindow){  
    mywindow.document.write(elem);
    let printerPaper = document.querySelector('#printerPaper');
    if(printerPaper){
        let px =  mywindow.document.body.querySelector('div').offsetHeight;
        printerPaper.setAttribute('data', px);
    }

    mywindow.document.close();
    mywindow.focus();
    mywindow.print();
    mywindow.close(); 
    // minusPaper();
}

// Функция скроллинга внутри блока
let jsScroll = document.getElementsByClassName('jsScroll');

if(jsScroll){
    [].forEach.call(jsScroll, function(item) {
        let startX, startY;
        let listener = function(e) {
            startX = this.scrollLeft + e.pageX;
            startY = this.scrollTop + e.pageY;
            item.addEventListener('mousemove', endListener);
        };

        let endListener = function(e) {
            this.scrollLeft = startX - e.pageX;
            this.scrollTop = startY - e.pageY;
            return false;
        };

        item.addEventListener('mousedown', listener);

        window.addEventListener("mouseup", function(){ 
            item.removeEventListener('mousemove', endListener);
        });
    });
}


function showMore(event) {
    for (let i = 0; i < showMoreButton.length; i++) {
        showMoreButton[i].classList.add('hidden')
        closeMoreButton[i].classList.remove('hidden')
    }
    optionList = document.querySelectorAll('.custom-option')

    for (let i = 0; i < optionList.length; i++) {
        optionList[i].classList.remove('opacity-0')
        if (optionList[i].id == 'showMoreRight') {
            optionList[i].classList.add('anim-products_right')
        } else {
            optionList[i].classList.add('anim-products_left')
        }
    }
    swipeAllSliders(0)
}
function closeMore(event) {
    for (let i = 0; i < showMoreButton.length; i++) {
        setTimeout(() =>
            showMoreButton[i].classList.remove('hidden')
            
        ,350);
    }
    optionList = document.querySelectorAll('.custom-option')
    for (let i = 0; i < optionList.length; i++) {
        optionList[i].classList.add('opacity-0')
        if (optionList[i].id == 'showMoreRight') {
            optionList[i].classList.remove('anim-products_right')
        } else {
            optionList[i].classList.remove('anim-products_left')
        }
    }
}