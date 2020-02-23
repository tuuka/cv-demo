
$(document).ready(function() {

    /* Setting working mode and static image loading */
    var mode = document.location.href.split('/').slice(-2,-1).pop();
    if ($.inArray(mode, ['image_recognition', 'semantic_segmentation', 'object_detection']) != -1) {
        var imgurl = '/static/images/' + mode + '-' + Math.floor((Math.random() * 8) + 1) + '.jpg'
    }

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


    function FillClassPredict(pred, empty=false){
        let prediction = pred['prediction'];
        if (mode == 'image_recognition') {
            for (let i = 0; i < $('div .pred-item').length; i++) {
                let elem = $("div .pred-item:nth-child(" + String(i + 1) + ")");
                if (!empty) {
                    elem.text(prediction[i][0] + '%-' + prediction[i][2].toLowerCase());
                    elem.css("width", String(prediction[i][0]) + "%");
                    elem.css("opacity", "1");
                } else {
                    elem.text('');
                    elem.css("opacity", "0");
                }
            }
        } else if (mode == 'semantic_segmentation'){
            let pred_items_count = $('div .pred-item').length;
            $('#img_seg').attr('src', '');
            for (let i = 0; i < pred_items_count; i++) {
                let elem = $("div .pred-item:nth-child(1)");
                elem.remove();
            }
            if (!empty) {
                let classes_map = pred['classes_map']
                $('#img_seg').attr('src', prediction);
                let base_div = $('#class-bars');
                for (let i = 0; i < classes_map.length; i++) {
                    if (classes_map[i][0] != 'background') {
                        let bar_text = classes_map[i][0];
                        let bar_color = classes_map[i][1];
                        let text_color = GetContrastTextColor(bar_color);
                        let elem = '<div class="progress-bar pred-item" role="progressbar" style="padding: 1px 10px 0 10px; width: 100% ; color: ' + text_color + '; background-color:' + bar_color + '">' + bar_text + '</div>';
                        base_div.append(elem);
                    }
                }
            }
        }
    }

    /* Brightness of color detecting to make text contrast*/
    function GetContrastTextColor(background_color) {
        let r, g, b, brightness,
            colour = background_color;
        if (colour.match(/^rgb/)) {
            colour = colour.match(/rgba?\(([^)]+)\)/)[1];
            colour = colour.split(/ *, */).map(Number);
            r = colour[0];
            g = colour[1];
            b = colour[2];
        } else if ('#' == colour[0] && 7 == colour.length) {
            r = parseInt(colour.slice(1, 3), 16);
            g = parseInt(colour.slice(3, 5), 16);
            b = parseInt(colour.slice(5, 7), 16);
        } else if ('#' == colour[0] && 4 == colour.length) {
            r = parseInt(colour[1] + colour[1], 16);
            g = parseInt(colour[2] + colour[2], 16);
            b = parseInt(colour[3] + colour[3], 16);
        }
        brightness = (r * 299 + g * 587 + b * 114) / 1000;
        if (brightness < 125) {return ("white");}
        else {return ("black");}
    }

    async function Predict(imgpost, urlpost){           // аргументы: файл и url. Маркер модели (название) будет в url
        let form_data = new FormData();                 // создаем форму для отправки
        form_data.append('file', imgpost);        // добавляем файл
        const response = await fetch (urlpost,{    // отправляем форму с файлом на сервер по
            method: 'POST',                             // заданному url
            body: form_data
        });
        return await response.json();                   // ждем ответа сервера и преобразовываем его в json
    }


    /* IMAGE PREVIEW CHANGE HANDLER - prediction is here */
    $('#imgpreview').bind('load', function (e) {                        // Привязка события к изменению изображения
        let ImgBlob = e.target.src;                                     // Извлечение изображения из превью
        FillClassPredict(0, true);                          // Очистка progress bars от старых данных
        BlockInput('block-input-modal', true);       // Блокировка ввода
        fetch(ImgBlob).then(i => i.blob()).then(function (b) {          // Преобразование изображения в Blob
            let urlpost = '/' + mode + '/predict?' +                    //Генерация ссылки на предикт с названием активной модели в аргументах
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
        let x = document.getElementsByClassName(classToBlock);
        let i;
        for (i = 0; i < x.length; i++) {
            if (activate){$(x[i]).addClass('overlay')}
            else {$(x[i]).removeClass('overlay')}
        }
    }


    /* Models selecting */
    $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
        $('#imgpreview').trigger('load');
    });


    //description text click
    $('#description-text').on("click",function(e) {
        //console.log(e);
        $('#PageModalDescription').modal('show');
    });


    $('#imgpreview').attr('src', imgurl);

});




