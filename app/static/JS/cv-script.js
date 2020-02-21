
$(document).ready(function() {

    var imgurl = '/static/images/image_recognition-' + Math.floor((Math.random() * 8) + 1) + '.jpg'

    /* IMAGE BROWSE HANDLER */
    $('#inputfile').bind('change', function () {
        let imgfile = this.files[0];
        let fileSize = imgfile.size / 1024 / 1024; // this gives in MB
        if (fileSize > 2) {
            $("#inputfile").val(null);
            alert("{{ _('file is too big. images more than 2MB are not allowed') }}");
            return
        }
        let ext = $('#inputfile').val().split('.').pop().toLowerCase();
        if ($.inArray(ext, ['jpg', 'jpeg', 'png', 'gif']) == -1) {
            $("#inputfile").val(null);
            alert("{{ _('only jpeg/jpg/png files are allowed!') }}");
            return
        }
        FillPreview($('#imgpreview'), imgfile);
    });


    /* CAMERA PICTURES HANDLER */
    $('#camera-input').bind('change', function () {
        FillPreview($('#imgpreview'), this.files[0]);
    });


    /* IMAGE PASTE HANDLER */
    var IMAGE_MIME_REGEX = /^image\/(p?jpeg|gif|png)$/i;
    $(document).on('paste', function (e) {
        if (!e.originalEvent.clipboardData || !e.originalEvent.clipboardData.items) return;
        let items = e.originalEvent.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (IMAGE_MIME_REGEX.test(items[i].type)) {
                let img = items[i].getAsFile();
                FillPreview($('#imgpreview'), img);
            }
        }
    });


    /* IMAGE URL PASTE HANDLER */
    $('#inputurl').bind("keypress", {}, urlkeypress); //Ловим нажатие клавиши, передаем событие в функцию.

    function urlkeypress(e) {
        var code = (e.keyCode ? e.keyCode : e.which); // Получаем код нажатой клавиши.
        var $thi = $(this), $inp = $thi.val();        // Получаем значение из объекта, в котором нажата клавиша.

        if (code == 13) {                             // Проверяем на "Enter".
            e.preventDefault();                       // Отменяем действие по умолчанию для "Enter", так как пропишем свое.
            $('#inputurl').val(null);                 // Очищаем поле объекта.

            fetch($inp).then(function (response) {    // Посылаем запрос на url, считанный из объекта, генерируя
                                                      // промис№1 в статусе "ожидание".
                                                      // В случае успеха (промис перешел в состояние "успешно")
                                                      // передаем ответ (response) в новую функцию, генерируя промис№2
                if (response.ok) {                    // Проверяем ответ на "ок"
                    return response.blob();           // и, в случае "ок", возвращаем изображение (blob) в промис№1
                } else {                              // в противном случае вызываем исключение
                    throw new Error('Network response is not ok.');
                }
            }).then(function (b) {                    // Переданное из промиса№2 изображение передаем в функцию FillPreview
                FillPreview($('#imgpreview'), b);
            }).catch(function (error) {               // Ловим исключения, выводим сообщения
                alert("Can't load this image. Please try another.");
                console.log('There was some problems with fetch operation:' + error.message);
            })
        }
    }


    function FillPreview(preview, imgblob) {
        let reader = new FileReader();
        reader.onloadend = function () {
            preview.attr('src', reader.result);
        };
        reader.readAsDataURL(imgblob);
    }


    function FillClassPredict(pred, empty=false){                           // Ответ сервера будет представлять собой словарь с несколькими ключами
        let prediction = pred['prediction'];                                // под ключом prediction находится список пар (класс - вероятность)
        for (let i = 0; i < $('div .pred-item').length; i++) {              // пробегаемся по progress-bars
            let elem = $("div .pred-item:nth-child(" + String(i + 1) + ")");
            if (!empty) {                                                   // Заполняя в соответствии с предсказаниями
                elem.text(prediction[i][0] + '%-' + prediction[i][2].toLowerCase());
                elem.css("width", String(prediction[i][0]) + "%")
                elem.css("opacity", "1")
            } else {                                                        // или очищаем
                elem.text('');
                elem.css("opacity", "0")
            }
        }
    }


    async function Predict(imgpost, urlpost){           // аргументы: файл и url. Маркер модели (название) будет в url
        let form_data = new FormData();                 // создаем форму для отправки
        form_data.append('file', imgpost);        // добавляем файл
        const response = await fetch (urlpost,{    // отправляем форму с файлом на сервер по
            method: 'POST',                            // заданному url
            body: form_data
        });
        return await response.json();                 // ждем ответа сервера и преобразовываем его в json
    }


    /* IMAGE PREVIEW CHANGE HANDLER - prediction is here */
    $('#imgpreview').bind('load', function (e) {                        // Привязка события к изменению изображения
        let ImgBlob = e.target.src;                                     // Извлечение изображения из превью
        FillClassPredict(0, true);                          // Очистка progress bars от старых данных
        BlockInput('block-input-modal', true);       // Блокировка ввода
        fetch(ImgBlob).then(i => i.blob()).then(function (b) {          // Преобразование изображения в Blob
            let urlpost = '/image_recognition/predict?' +               //Генерация ссылки на предикт с названием активной модели в аргументах
              $('#models-tab a[aria-selected="true"]')[0].href.split('?').pop();
            Predict(b, urlpost)                                         // Отправка данных на сервер, ожидание ответа
                .then(function (pred) {                        // Ответ получен
                    if (!pred['error']) {                               // Проверяем предикт
                        FillClassPredict(pred);                         // Отображаем предсказания, если модель на сервере отработала без ошибок
                    } else {
                        alert(pred['error']);                           // В противном случае выводим сообщение об ошибке
                    }
                    BlockInput('block-input-modal', false);             // Убираем блокировку
                }).catch(function (error) {                             // В случае неудачного fetch-запроса убираем блокировку
                    BlockInput('block-input-modal', false);             // и выводим в консоль отладочное сообщение
                    console.log('There has been problem with fetch operation when predicting:' + error.message);
            });
        });
    });


    /* Making some areas blocked until necessary action done */
    function BlockInput(classToBlock, activate=false) {
        //console.log(classToBlock);
        let x = document.getElementsByClassName(classToBlock);
        let i;
        for (i = 0; i < x.length; i++) {
            //console.log(x[i]);
            if (activate){$(x[i]).addClass('overlay')}
            else {$(x[i]).removeClass('overlay')}
        }
    }


    /* Models selecting & descriptions showing */
    $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
        $('#imgpreview').trigger('load');
    });


    $('#imgpreview').attr('src', imgurl);
    $('#imgpreview').trigger('load');

});




