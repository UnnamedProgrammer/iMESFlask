// Фукнция управления модальным окном с ввода цифрового значения (например, количества)
let numberModal = document.getElementById('numberModal')
let key = document.querySelectorAll('.keyboard__key');
let display = document.querySelector('.modal__input-number');
let enter = document.querySelector('.modal__enter-button')
let del = document.querySelector('.keyboard__key_del');

let productList = document.querySelector('#currentProductList')

let productData = null

let wasteData = null

let defectCount = 0
let defectWeight = 0

function numberModalControl(event){
    numberModal.classList.toggle('hidden');
    display.textContent = '';
    let buttonID = event.target.id;
    let lastID = ''
    for(let k of key){
        k.onclick = function(){
            display.classList.remove('outline-red')
            display.textContent += k.textContent;
        }
    }
    if (buttonID == 'idleValidClousersData')
    {
        lastID = enter.id
        enter.id = 'idleValidClousersData'
    }
    // При нажатии клавиши "Ввод" переносит значение из строки ввода в строку со значением
    // Строка в которую будут вносится введенные данные должна иметь ID кнопки отрытия окна +Data, вида: exmapleData (например, wasteData)
    enter.onclick = function(){
        data = document.getElementById(buttonID+'Data');

        if(display.textContent != "")
        {
            if(enter.id == 'addWasteWeight'){
                let entered_waste_weight = document.getElementById('inputDefect').textContent;
                var socket = io();
                socket.emit('product_wastes', [productData[0], wasteData[0], entered_waste_weight]);
                $(table).find('tbody').append('<tr> <td id="wasteProductData" data-proddataoid="'+ productData[0] +'">'+ productData[1] +'</td> <td class="table-warning" id="wasteData" data-wasteoid="'+ wasteData[0] +'">'+ wasteData[1] +'</td> <td></td> <td id="wasteWeight">'+ display.textContent +'<td></td> <td>'+ clock +'</td> <td>'+ current_user +'</td> </tr>'); // Добавление новой строки в таблицу
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
                enter.id = 'defectEnterCount';
                let socket = io();
                socket.emit('product_defect', [productData[0], defectWeight, defectCount]);
                $(table).find('tbody').append('<tr> <td id="defectProductData" data-proddataoid="'+ productData[0] +'">'+ productData[1] +'</td> <td class="red"> Брак </td> <td id="defectCount">'+ defectCount +'</td> <td id="defectWeight">'+ defectWeight +'<td></td> <td>'+ clock +'</td> <td>'+ current_user +'</td> </tr>'); // Добавление новой строки в таблицу
            }

            else if (enter.id == 'productWeight')
            {
                productWeight = display.textContent;
                let entered_weight = document.getElementById('inputWeight').textContent;
                let socket = io();
                clock = document.getElementById('clock').innerHTML
                socket.emit('product_weight_entering', [entered_weight, productData[0]]);
                $(table).find('tbody').append('<tr> <td id="weightProductData" data-proddataoid="'+ productData[0] +'">'+ productData[1] +'</td> <td class="green" id="productWeightData">'+ productWeight +'</td> <td>'+clock+'</td> <td>'+ current_user +'</td> </tr>');
            }

            else if(enter.id == 'defectIdleEnterCount')
            {
                defectCount = display.textContent;
                enter.innerHTML = 'ВВОД КГ.'
                enter.id = 'defectIdleEnterWeight';
                numberModalControl(event);
            }

            else if(enter.id == 'defectIdleEnterWeight')
            {
                defectWeight = display.textContent;
                enter.id = 'defectEnterCount';
                data = [productData, defectWeight, defectCount]
                addEnteredData(data, 'defect')
            }

            else if (enter.id == 'addIdleWasteWeight')
            {
                let enteredWasteWeight = document.getElementById('inputDefect').textContent;
                let data = [productData, wasteData, enteredWasteWeight]
                addEnteredData(data,'waste')
            } 

            else if(event.target.tagName == 'INPUT')
            {
                event.target.value = display.textContent;
            }

            else if(enter.id == 'idleValidClousersData')
            {
                event.target.value = display.textContent;
                enter.id = lastID
            }

            else
            {
                data.textContent = display.textContent;
            }

            numberModal.classList.toggle('hidden');
            display.textContent = '';
        } else {
            showError('Введите значение!')
            display.classList.add('outline-red')
        }
    }
    // Функция удаления последнего символа
    del.onclick = function(){
        display.textContent = display.textContent = display.textContent.substring(0, display.textContent.length - 1);
    }
}

function selectProduct(event) {
    productData = [event.target.dataset.proddataoid, event.target.dataset.prodname]
    productList.classList.toggle('hidden')
    if (event.target.dataset.target == 'wasteSelect'){
        document.getElementById('addWaste').classList.toggle('hidden')
        event.target.dataset.target = ''
    }

    else if (event.target.dataset.target == 'addProductWeight') {
        numberModalControl(event)
        event.target.dataset.target = ''
    }

    else if (event.target.dataset.target == 'addIdleWaste'){
        document.getElementById('addWaste').classList.toggle('hidden')
    }
    
    else if (event.target.dataset.target == 'addIdleDefect'){
        enter.id = 'defectIdleEnterCount'
        enter.innerHTML = 'ВВОД КОЛ.'
        numberModalControl(event)
        event.target.dataset.target = ''
    }

    else {
        enter.id = 'defectEnterCount'
        enter.innerHTML = 'ВВОД КОЛ.'
        numberModalControl(event)
        event.target.dataset.target = ''
    }
}

function selectWaste(event) {
    wasteData = [event.target.dataset.wasteoid, event.target.dataset.wastename]
    document.getElementById('addWaste').classList.toggle('hidden')

    enter.innerHTML = 'ВВОД КГ.'
    enter.id = 'addWasteWeight'

    numberModalControl(event)
}
