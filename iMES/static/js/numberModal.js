// Фукнция управления модальным окном с ввода цифрового значения (например, количества)
let numberModal = document.getElementById('numberModal')
let key = document.querySelectorAll('.keyboard__key');
let display = document.querySelector('.modal__input-number');
let enter = document.querySelector('.modal__enter-button')
let del = document.querySelector('.keyboard__key_del');

let productList = document.querySelector('#currentProductList')

let productData = null

let defectCount = 0
let defectWeight = 0

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
        clock = document.getElementById('clock').innerHTML

        if(display.textContent != "")
        {
            if(event.target.id == 'addWasteWeight'){
                let count = event.target.parentNode.parentNode.cells[2];
                count.innerHTML = display.textContent;
            }
            
            else if(enter.id == 'defectEnterCount')
            {
                defectCount = display.textContent;
                enter.innerHTML = 'ВВОД КГ.'
                enter.id = 'defectEnterWeight';
                numberModalControl(event);
            }

            else if(enter.id == 'defectEnterWeight')
            {
                defectWeight = display.textContent;
                selectCurrentProductDefect();
                enter.id = 'defectEnterCount';
            }

            else if (enter.id == 'productWeight') {
                productData = display.textContent;
                productList.classList.toggle('hidden')
            }

            else if(event.target.tagName == 'INPUT')
            {
                event.target.value = display.textContent;
            }

            else
            {
                data.textContent = display.textContent;
            }

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

// Ввод веса с выбором продукта
function selectCurrentProductWeight(event) {
    let currentProduct = event.target.dataset.selectproduct
    $(table).find('tbody').append('<tr> <td>'+ currentProduct +'</td> <td class="green" id="productWeightData">'+ productData +'</td> <td>'+clock+'</td> <td>'+ current_user +'</td> </tr>'); // Добавление новой строки в таблицу
    productList.classList.toggle('hidden')
}

// --------------- Ввод отхода с выбором продукта ---------------
// Получение данных о выбранном отходе, при нажатии на кнопку "Выбрать"
function selectCurrentProductWaste(event) {
    let selectedWasteData = [event.target.parentNode.parentNode.cells[1].dataset.oid, event.target.parentNode.parentNode.cells[1].innerHTML] // Массив с даннымы отхода [Oid, Name]
    document.getElementById(event.target.id).classList.toggle('hidden') // Скрыть модальное окно с выбором отходов
    addWasteData(selectedWasteData) // Передача массива данных отхода в функцию выбора продутк
    
}

function addWasteData(data) {
    productList.classList.toggle('hidden') // Отображение модульного окна с выбором продуктов для добавления отхода

    document.addEventListener("click", function(e) {
        if (e.target.id == ('addWasteButton')) {
            let selectedProductData = [e.target.parentNode.parentNode.cells[1].dataset.oid, e.target.parentNode.parentNode.cells[1].innerHTML] // Массив с даннымы продукта [Oid, Name]
            $(table).find('tbody').append('<tr id="wasteData"> <td data-productoid="'+selectedProductData[0]+'">'+ selectedProductData[1] +'</td> <td data-wasteoid="'+data[0]+'" style="overflow:hidden">'+ data[1] +'</td> <td id="wasteCount_Data"></td>   <td class="nopadding col-2 table__button"><button type="button" class="btn__table" id="addWasteWeight" onClick="numberModalControl(event)">Ввод</button>/td></tr>'); // Добавление новой строки в таблицу
            productList.classList.toggle('hidden')
        }
    });
}
// ------------------------------------------------------------

// Ввод отхода с выбором продукта
function selectCurrentProductDefect() {
    productList.classList.toggle('hidden')

    document.addEventListener("click", function(e) {
        if (e.target.id == ('addWasteButton')) {
            let selectedProductData = [e.target.parentNode.parentNode.cells[1].dataset.oid, e.target.parentNode.parentNode.cells[1].innerHTML] // Массив с даннымы продукта [Oid, Name]
            $(table).find('tbody').append('<tr id="defectData"> <td data-productoid="'+selectedProductData[0]+'">'+ selectedProductData[1] +' <td class="red"> Брак </td> <td id="defectCount_Data">'+ defectCount +'</td> <td id="defectWeight_Data">'+defectWeight+'</td> <td id="defectReason_Data"></td> <td id="defectTime_Data">'+ clock +'</td> <td id="defectUser_Data">'+ current_user +'</td>'); // Добавление новой строки в таблицу
            productList.classList.toggle('hidden')
        }
    });
}