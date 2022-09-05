let numberModal = document.getElementById('numberModal')

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

// Фукнция управления модальным окном с ввода цифрового значения (например, количества)
let key = document.querySelectorAll('.keyboard__key');
let display = document.querySelector('.modal__input-number');
let enter = document.querySelector('.modal__enter-button')
let del = document.querySelector('.keyboard__key_del');

function numberModalControl(event){
    numberModal.classList.toggle('hidden');
    display.textContent = '';
    let buttonID = event.target.id;
    for(let k of key){
        k.onclick = function(){
            display.classList.remove('outline-red')
            display.textContent += k.textContent;
        }
    }
    // При нажатии клавиши "Ввод" переносит значение из строки ввода в строку со значением
    // Строка в которую будут вносится введенные данные должна иметь ID кнопки отрытия окна +Data, вида: exmapleData (например, wasteData)
    enter.onclick = function(){
        data = document.getElementById(buttonID+'Data');
        if(display.textContent != "")
        {
            data.textContent = display.textContent;
            numberModal.classList.toggle('hidden');
            display.textContent = '';
        } else {
            alert('Введите значение!')
            display.classList.add('outline-red')
        }
    }
    // Функция удаления последнего символа
    del.onclick = function(){
        display.textContent = display.textContent = display.textContent.substring(0, display.textContent.length - 1);
    }
}