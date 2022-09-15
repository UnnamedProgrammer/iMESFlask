// Фукнция управления модальным окном с ввода цифрового значения (например, количества)
let numberModal = document.getElementById('numberModal')
let key = document.querySelectorAll('.keyboard__key');
let display = document.querySelector('.modal__input-number');
let enter = document.querySelector('.modal__enter-button')
let del = document.querySelector('.keyboard__key_del');

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
                count.dataset.weight = display.textContent;
            }
            
            else if(enter.id == 'defectEnterCount')
            {
                defectCount = display.textContent;
                enter.innerHTML = 'ВВОД КГ.'
                enter.id = 'defectEnterWeight';
                numberModalControl(event);
                console.log(defectCount)
            }

            else if(enter.id == 'defectEnterWeight')
            {
                defectWeight = display.textContent;
                enter.id = 'defectEnterCount';
                $(wasteDefectTable).find('tbody').append('<tr> <td>Поддон полимерного контейнера  Д202 900/1080</td> <td class="red">Брак</td> <td id="defectCount_Data">'+ defectCount +'</td> <td id="defectWeight_Data">'+ defectWeight +'</td> <td></td> <td>'+clock+'</td> <td>'+ current_user +'</td> </tr>'); // Добавление новой строки в таблицу
            }

            else if (enter.id == 'productWeight') {
                let productWeight = display.textContent;
                $(productWeightTable).find('tbody').append('<tr> <td>Поддон полимерного контейнера  Д202 900/1080</td> <td class="green" id="productWeightData">'+ productWeight +'</td> <td>'+clock+'</td> <td>'+ current_user +'</td> </tr>'); // Добавление новой строки в таблицу
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