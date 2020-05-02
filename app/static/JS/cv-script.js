$(document).ready(function() {

    var IMAGE_MIME_REGEX = /^image\/(p?jpeg|gif|png)$/i;

    /* Setting working mode and static image loading */
    var mode = document.location.href.split('/').slice(-2,-1).pop();
    if ($.inArray(mode, ['image_recognition', 'semantic_segmentation', 'object_detection']) != -1) {
        var imgurl = '/static/images/' + mode + '-' + Math.floor((Math.random() * 8) + 1) + '.jpg'
    }

    /* IMAGE URL PASTE HANDLER */
    $('#inputurl').bind("keypress", {}, urlkeypress);

    function urlkeypress(e) {
        var code = (e.keyCode ? e.keyCode : e.which);
        var $thi = $(this), $inp = $thi.val();
        if (code == 13) { //check Enter
            e.preventDefault();
            $('#inputurl').val(null);
            fetch($inp).then(function (response) {
                if (response.ok) {
                    return response.blob();
                } else {
                    throw new Error('Network response is not ok.');
                }
            }).then(function (b) {
                FillPreview($('#imgpreview'), b);
            }).catch(function (error) {
                alert("Can't load this image. Please try another.");
                console.log('There was some problems with fetch operation:' + error.message);
            })
        }
    }

    /* CAMERA PICTURES HANDLER */
    $('#camera-input').bind('change', function () {
        FillPreview($('#imgpreview'), this.files[0]);
    });

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

    /* IMAGE PASTE HANDLER */
    $(document).on('paste', function (e) {
        if (!e.originalEvent.clipboardData || !e.originalEvent.clipboardData.items) return;
        let items = e.originalEvent.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (IMAGE_MIME_REGEX.test(items[i].type)) {
                let img = items[i].getAsFile();
                //console.log(img);
                FillPreview($('#imgpreview'), img);
            }
        }
    });


    /* IMAGE PREVIEW CHANGE HANDLER - prediction is here */
    $('#imgpreview').bind('load', function (e) {
        let ImgBlob = e.target.src;
        FillClassPredict(0, true);
        BlockInput('block-input-modal', true);
        fetch(ImgBlob).then(i => i.blob()).then(function (b) {
            let urlpost = '/' + mode + '/predict?' + $('#models-tab a[aria-selected="true"]')[0].href.split('?').pop();
            Predict(b, urlpost)
                .then(function (pred) {
                    if (!pred['error']) {
                        FillClassPredict(pred);
                    } else {
                        alert(pred['error']);
                    }
                    BlockInput('block-input-modal', false);
                }).catch(function (error) {
                    BlockInput('block-input-modal', false);
                    console.log('There has been problem with fetch operation when predicting:' + error.message);
            });
        });
    });


    async function Predict(imgpost, urlpost){
        let form_data = new FormData();
        form_data.append('file', imgpost);
        const response = await fetch (urlpost,{
            method: 'POST',
            body: form_data
        });
        return await response.json();
    }

    /* CLICK ON PREDICTION TEXT TO TRANSLATE HANDLER */
    $('div .pred-item').on('click', Pred_Item_Click);

    function Pred_Item_Click(e) {
        DetectLanguage($('div .pred-item:first').text().split('-').pop()).then(function (lg) {
            if (lg && (lg != g_locale)) {
                for (let i = 0; i < $('div .pred-item').length; i++) {
                    let elem = $("div .pred-item:nth-child(" + String(i + 1) + ")");
                    elem.addClass('progress-bar-striped');
                    elem.addClass('progress-bar-animated');
                    Translate(elem.text().split('-').pop(), lg, g_locale)
                        .then(function (response) {
                            if (response.ok) {
                                return response.json()
                            }
                        }).then(function (translation) {
                        let old = elem.text().split('-').slice(0, -1);
                        //console.log(mode);
                        if (mode == 'image_recognition') {
                            elem.text(old + '-' + translation['text'].toLowerCase());
                        } else if (mode == 'semantic_segmentation') {
                            elem.text(translation['text'].toLowerCase());
                        }
                        elem.removeClass('progress-bar-striped');
                        elem.removeClass('progress-bar-animated');
                    })
                }
            }
        })
    }


    function FillPreview(preview, imgblob) {
        let reader = new FileReader();
        reader.onloadend = function () {
            preview.attr('src', reader.result);
        };
        reader.readAsDataURL(imgblob);
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

    /* Filling all with predicted result. Filling color bars with predicted classes' text */
    function FillClassPredict(pred, empty=false){
        let prediction = pred['prediction'];
        try {
            let elem = $('.time-elem');
            elem.remove()
        }
        catch (e) {}
        if ((!empty) &&
                ($.inArray(mode, ['image_recognition',
                              'semantic_segmentation',
                              'object_detection']) != -1) &&
                (prediction['time'] != 0)) {
            let cont = $(".preview-predict-form");
            let timeelem = '<p class="time-elem" ' +
                'style="position:absolute; left: 0; top: 0; padding: 0 10px; ' +
                'color: #000; background-color: rgba(255,255,255,0.3);' +
                'font-size: 10px">' + prediction['time'] + ' sec. (' +
                 pred['time'] + ')</p>';
            cont.append(timeelem)
        }
        if (mode == 'image_recognition') {
            for (let i = 0; i < $('div .pred-item').length; i++) {
                let elem = $("div .pred-item:nth-child(" + String(i + 1) + ")");
                if (!empty) {
                    elem.text(prediction['scores'][i] + '%-' + prediction['name'][i].toLowerCase());
                    elem.css("width", String(prediction['scores'][i]) + "%");
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
                let classes_map = prediction['classes']
                $('#img_seg').attr('src', prediction['img_seg']);
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
                $('div .pred-item').on('click', Pred_Item_Click); /* Register onclick handler on bars just created */
            }
        } else if (mode == 'object_detection') {
            let c = document.getElementById("detection_canvas");
            c.style.opacity = "1.0";
            let ctx = c.getContext("2d");
            ctx.clearRect(0,0, c.width, c.height);
            $('#img_seg').attr('src', '');
            if (!empty) {
                let imgpreview = document.getElementById("imgpreview");
                c.setAttribute('width', imgpreview.width);
                c.setAttribute('height', imgpreview.height);
                for (let i = 0; i < prediction['boxes'].length; i++) {
                    let x1 = Math.round(c.width * prediction['boxes'][i][0]);
                    let y1 = Math.round(c.height * prediction['boxes'][i][1]);
                    let x2 = Math.round(c.width * prediction['boxes'][i][2]);
                    let y2 = Math.round(c.height * prediction['boxes'][i][3]);
                    DrawRect(ctx, x1, y1, x2, y2,
                            prediction['colors'][i],
                            //'#FFFFFF',
                            prediction['labels'][i],
                            parseInt(c.height*0.03)); //text height
                }
                if ('masks' in prediction) {
                    $('#img_seg').attr('src', prediction['masks']);
                    $('#img_seg').css("opacity", "0.4"); //transparency of mask
                } else {
                    //c.style.opacity = "1";
                }
            }
        }
    }

    function DrawRect(ctx, x1, y1, x2, y2, color, text='', text_size=10, text_pad=5, shadow=1){
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.setLineDash([5, 3]);
        ctx.font = text_size.toString(10) + "px sans-serif";
        let text_width = ctx.measureText(text).width;
        text_width = (text_width > parseInt((x2-x1)*0.8)) ? parseInt((x2-x1)*0.8) : text_width;
        ctx.moveTo(x1 + text_pad, y1);
        ctx.lineTo(x1, y1);
        ctx.lineTo(x1, y2);
        ctx.lineTo(x2, y2);
        ctx.lineTo(x2, y1);
        ctx.lineTo(x1 + text_pad + text_width, y1);
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        ctx.shadowColor = GetContrastTextColor(color);
        ctx.shadowBlur = shadow;
        ctx.fillText(text, x1+text_pad, y1+parseInt(text_size*0.3), text_width);
    }


    async function DetectLanguage(probe){
        let form_data = new FormData();
        form_data.append('text', probe);
        const response = await fetch ('/lgdetect',{
            method: 'POST',
            body: form_data
        });
        let lg = await response.json();
        return lg['lg']
    }

    function Translate(probe, sourcelg, destlg){
        let form_data = new FormData();
        form_data.append('text', probe);
        form_data.append('source_language', sourcelg);
        form_data.append('dest_language', destlg);
        return fetch ('/translate',{
            method: 'POST',
            body: form_data
        })
    }

    /* Making some areas blocked until necessary action done */
    function BlockInput(classToBlock, activate=false) {
        let x = document.getElementsByClassName(classToBlock);
        let i;
        for (i = 0; i < x.length; i++) {
            if (activate){$(x[i]).addClass('overlay')}
            else {$(x[i]).removeClass('overlay')}
        }
    }

    // Unused for now
    function ElemBlink(element, basetext, blinktext, interval, blink=false){
        function timedChange() {
            $(element).fadeOut(100, function(){$(element).fadeIn(100)});
            t = setTimeout(timedChange, interval);
        }
        if (!blink){
            clearTimeout(t);
            element.text = basetext;
        } else{
           $(element).fadeOut(100, function(){element.text = blinktext});
            timedChange()
        }
    }

    /* Models selecting & descriptions showing */
    $('a[data-toggle="pill"]').on('shown.bs.tab', function (e) {
        /* Simple switching without model-route using
        *  just trigger image load event to load and predict existing in preview image */
        let ext = $('#imgpreview')[0].src.split('.').pop().toLowerCase();
        if ($.inArray(ext, ['html']) == -1) {
            $('#imgpreview').trigger('load');
        } else{ /* load image to preview when page is just opened */
            $('#imgpreview').attr('src', imgurl);
        }
    });

    /* Activating model switching first time after page is loaded to
      predict static image in imgurl variable*/
    $('a[data-target="#model1-href"]').trigger('shown.bs.tab');
});

//description text click
$('#description-text').on("click",function(e) {
    $('#PageModalDescription').modal('show');
});

//About Timeline "more" click
$('.timeline_more').on("click",function(e) {
    let i = e.target.id.split('timeline').pop();
    $("#TimeLineModal" + String(i)).modal('show');
});


//Canvas clicking - bounding boxes hide/show
$('#detection_canvas').on("click",function(e) {
    let canv = e.target;
    canv.style.opacity  = (canv.style.opacity == 0) ? 1.0 : 0.0
});

