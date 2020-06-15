

$(document).ready(function () {
  /* Change responsive font with respect to parent width */
  /* Was using it some time to make a responsive page design */
  // let responsiveFontElems = document.querySelectorAll('[data-responsive-font]');
  // changeFontSize(responsiveFontElems);
  // $(window).resize(function () {
  //   changeFontSize(responsiveFontElems);
  // });
  // function changeFontSize(classesToChange, multiplier = 0.05) {
  //   let maxSizeAmongnAll = 0;
  //   // exclude the possibility of zero-width due to hidden elements
  //   // just find max width
  //   for (let i = 0; i < classesToChange.length; i++) {
  //     if (classesToChange[i].parentElement.offsetWidth > maxSizeAmongnAll) {
  //       maxSizeAmongnAll = classesToChange[i].parentElement.offsetWidth;
  //     }
  //   }
  //   // value of font size for elements with zero width
  //   maxSizeAmongnAll = Math.round(maxSizeAmongnAll * multiplier);
  //   if (classesToChange.length > 0) {
  //     for (let i = 0; i < classesToChange.length; i++) {
  //       let newTextSize = Math.round(classesToChange[i].parentElement.offsetWidth * multiplier);
  //       if (newTextSize == 0) {
  //         newTextSize = maxSizeAmongnAll;
  //       }
  //       // extract max font size for text
  //       let maxFontSize = parseInt(classesToChange[i].getAttribute('data-responsive-font'));
  //       newTextSize = newTextSize > maxFontSize ? maxFontSize : newTextSize;
  //       classesToChange[i].style.fontSize = String(newTextSize) + 'px';
  //     }
  //   }
  // }
  /*  //Change responsive font with respect to parent width */

  /* Make all necessary links to open in new page */
  $('a')
    .not('.nav-link, .carousel-control-next, .carousel-control-prev, .learn-more-btn, .navbar-brand')
    .attr('target', '_blank');

  /* A flag to block control while image is being processed */
  var imageGettingProcessed = false;

  /* Sometimes img onload event does not fire. Fire it explicitly */
  var imageProcessedFirstTime = true;
  setTimeout(function () {
    if (imageProcessedFirstTime && $.inArray(mode, work_modes) != -1) {
      //console.log('Fire prediction explicitly!');
      $('.img-src').trigger('load');
    }
  }, 500);

  /* Heh to RGB function */
  const hexToRgb = (hex) =>
    hex
      .replace(/^#?([a-f\d])([a-f\d])([a-f\d])$/i, (m, r, g, b) => '#' + r + r + g + g + b + b)
      .substring(1)
      .match(/.{2}/g)
      .map((x) => parseInt(x, 16));

  /* Set mode link active in main navigation menu*/
  let modeLinks = $('[data-mode]');
  for (let i = 0; i < modeLinks.length; i++) {
    if (modeLinks[i].getAttribute('data-mode') == mode) {
      modeLinks[i].classList.add('active');
    } else {
      modeLinks[i].classList.remove('active');
    }
  }

  // help-link click => show modal description
  // help link from main menu is linking this modal window on ID, so in JS we will use this ID too
  $('.help-link').click(() => $('#ModeModalDescription').modal('show'));

  /* Fetching image from url to Base64 */
  const urlToBase64 = (url) =>
    fetch(url)
      .then((r) => r.blob())
      .then((blob) => blobToBase64(blob));

  /* Base64 coding of Blob image object with size and type checking */
  const blobToBase64 = (blob) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(checkBlob(blob));
    });

  /* Check if Blob is an image and has appropriate size */
  const checkBlob = (blob) => {
    if (/^image\/(p?jpeg|gif|png|webp)$/i.test(blob.type)) {
      if (blob.size / 1024 / 1024 < 2) {
        return blob;
      } else {
        alert(file_too_big_alert);
        throw new Error('Image with size more then 2MB is not allowed!.');
      }
    } else {
      alert(only_image_allowed_alert);
      throw new Error('It`s not an image!.');
    }
  };

  // IMAGE URL PASTE HANDLER
  // url-input is labeled with ID, so use this ID for selection
  $('#input-url').on('keypress', function (e) {
    if (imageGettingProcessed) return;
    if (e.keyCode == 13) {
      //check Enter
      e.preventDefault();
      let url = 'https://cors-anywhere.herokuapp.com/' + $(this).val();
      $(this).val(null);
      urlToBase64(url)
        .then((img) => $('.img-src').attr('src', img))
        .catch((error) => console.log(`Fetching an image from url ${error}`));
    }
  });

  /* CAMERA IMAGE HANDLER */
  // camera-input is labeled with ID, so use this ID for selection
  $('#camera-input').on('change', function () {
    if (imageGettingProcessed) return;
    blobToBase64(this.files[0])
      .then((img) => $('.img-src').attr('src', img))
      .catch((error) => console.log(`Fetching an image from a camera ${error}`));
  });

  /* IMAGE BROWSE HANDLER */
  // file-input is labeled with ID, so use this ID for selection
  $('#input-file').on('change', function () {
    if (imageGettingProcessed) return;
    blobToBase64(this.files[0])
      .then((img) => $('.img-src').attr('src', img))
      .catch((error) => console.log(`Fetching an image from local storage ${error}`));
  });

  /* IMAGE PASTE HANDLER */
  $(document).on('paste', function (e) {
    if (imageGettingProcessed) return;
    if (!e.originalEvent.clipboardData || !e.originalEvent.clipboardData.items) return;
    let items = e.originalEvent.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (/^image\/(p?jpeg|gif|png|webp)$/i.test(items[i].type)) {
        // let img = items[i].getAsFile();
        blobToBase64(items[i].getAsFile())
          .then((img) => $('.img-src').attr('src', img))
          .catch((error) => console.log(`Fetching an image from a clipboard ${error}`));
      }
    }
  });

  /* Prevent clicking when image is being processed */
  $('a[data-toggle="tab"], #camera-input, #input-file, #input-url').on('click', function (e) {
    if (imageGettingProcessed) {
      e.preventDefault();
      e.stopPropagation();
      let popupElem = `
      <div class="popup-elem"
           style="border: 1px solid black; 
                  font-size: 0.8em;
                  border-radius: 0.3em; 
                  background-color: rgba(255, 255, 255, 0.85);
                  position: absolute;
                  left: ${e.clientX + 25}px;
                  top: ${e.clientY - 60}px;
                  width: 20em;
                  padding: 0.1em 0.4em;
                  z-index: 200">
      ${image_processing_in_progress_alert}
      </div>
      `;
      $(`${popupElem}`).appendTo('body');
      if ($(window).width() < $('.popup-elem').width() + e.clientX + 25) {
        $('.popup-elem').css('left', e.clientX - $('.popup-elem').width() - 25);
      }
      setTimeout(function () {
        $('.popup-elem').fadeOut(700, function () {
          $('.popup-elem').remove();
        });
      }, 1500);
    }
  });

  /* Model selection. Trigger image load event to start prediction */
  $('a[data-toggle="tab"]').on('shown.bs.tab', function () {
    $('.img-src').trigger('load');
  });

  /* IMAGE PREVIEW CHANGE HANDLER - prediction is here */
  $('.img-src').on('load', function (e) {
    imageProcessedFirstTime = false;
    fillResultFields();
    blockInput();
    let imgBlob = e.target.src;
    let url = lambda_url;
    urlToBase64(imgBlob).then((img) => {
      //console.log('predict url: ', url);
      let active_model = $('.model-change-form__tabs-captions a[aria-selected="true"]');
      fetch(url, {
        method: 'POST',
        body: JSON.stringify({
          size: active_model.data('size'),
          model: active_model.attr('aria-controls'),
          data: img,
          threshold: active_model.data('threshold'),
          labels: labels[active_model.data('dataset')],
          topN: topN,
        }),
      })
        .then((r) => r.json())
        .then((data) => {
          blockInput(false);
          if (data['status'] != 'OK') throw new Error('Prediction status is not OK!.');
          else {
            fillResultFields(data['data']);
          }
        })
        .catch((e) => {
          blockInput(false);
          console.log(`Error in main fetch block: ${e}`);
        });
    });
  });

  /* Brightness of color detecting to make text contrast*/
  function GetContrastTextColor(background_color) {
    let r,
      g,
      b,
      brightness,
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
    if (brightness < 125) {
      return 'white';
    } else {
      return 'black';
    }
  }

  /* Filling all placeholders with predicted result. */
  function fillResultFields(prediction = null) {
    if (!prediction) {
      $('.prediction-bars, .img-seg, .img-canvas, .time-elem').not('.hidden').addClass('hidden');
    } else {
      prediction = JSON.parse(prediction);
      $('.preview').find('.pred-bar').remove();
      $('.time-elem').remove();
      let timeelem = `<p class="time-elem">${prediction.time['all_time']}sec. (prediction:${prediction.time['model_prediction_time']}sec.; loading:${prediction.time['model_load_time']}sec.; session creation: ${prediction.time['session_creation_time']}sec.)</p>`;
      $('.preview').append(timeelem);
      let pred_bars_wrapper = $('.prediction-bars');
      if ($.inArray(mode, work_modes) == 0) {
        //image recognition
        pred_bars_wrapper.removeClass('hidden');
        for (let i = 0; i < prediction['scores'].length; i++) {
          let bar = `<div class="pred-bar" role="progressbar" 
                       style="background-color:${prediction.colors[i]};">
                       ${prediction.scores[i]}%-${prediction.labels[i].toLowerCase()}
                     </div>`;
          pred_bars_wrapper.append(bar);
          /* Make width changing smooth */
          setTimeout(async function () {
            pred_bars_wrapper.children()[i].style.width = `${prediction['scores'][i]}%`;
          }, 10);
        }
      } // //image recognition
      else if ($.inArray(mode, work_modes) == 1) {
        //semantic segmentation
        pred_bars_wrapper.removeClass('hidden');
        $('.img-seg').attr('src', prediction.masks);
        $('.img-seg').removeClass('hidden');
        for (let i = 0; i < prediction.labels.length; i++) {
          if (prediction.labels[i] != 'background') {
            let text_color = GetContrastTextColor(prediction['colors'][i]);
            let bar = `<div class="pred-bar" 
                         role="progressbar" 
                         style="width: 100%; 
                                padding: 0 0.2em; 
                                background-color: ${prediction.colors[i]}; 
                                color: ${text_color};">
                         ${prediction.labels[i].toLowerCase()}
                       </div>`;
            pred_bars_wrapper.append(bar);
          }
        }
      } // //semantic segmentation
      else if ($.inArray(mode, work_modes) == 2) {
        //object detection
        $('.img-seg').attr('src', prediction.masks);
        $('.img-seg, .img-canvas').removeClass('hidden');
        let c = $('.img-canvas')[0];
        c.setAttribute('width', $('.img-src')[0].width);
        c.setAttribute('height', $('.img-src')[0].height);
        let ctx = c.getContext('2d');
        ctx.clearRect(0, 0, c.width, c.height);
        for (let i = 0; i < prediction['boxes'].length; i++) {
          let x1 = Math.round(c.width * prediction.boxes[i][0]);
          let y1 = Math.round(c.height * prediction.boxes[i][1]);
          let x2 = Math.round(c.width * prediction.boxes[i][2]);
          let y2 = Math.round(c.height * prediction.boxes[i][3]);
          DrawRect(ctx, x1, y1, x2, y2, prediction.colors[i],
            prediction.labels[i],
            // labels text height calculation:
            parseInt(Math.min(Math.max(c.height * 0.03, 10), 16)));
        }
      } // //object detection
    }
  }

  function DrawRect(ctx, x1, y1, x2, y2, color, text = '', text_size = 10, text_pad = 5, opacity = 0.5) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.setLineDash([5, 3]);
    ctx.font = text_size.toString(10) + 'px Oswald, sans-serif';
    let text_width = ctx.measureText(text).width;
    text_width = text_width > parseInt((x2 - x1) * 0.8) ? parseInt((x2 - x1) * 0.8) : text_width;
    ctx.moveTo(x1 + text_pad, y1);
    ctx.lineTo(x1, y1);
    ctx.lineTo(x1, y2);
    ctx.lineTo(x2, y2);
    ctx.lineTo(x2, y1);
    ctx.lineTo(x1 + text_pad + text_width, y1);
    ctx.stroke();
    // ctx.fillStyle = 'rgba(' + hexToRgb(color).join(', ') + ', ' + opacity)';
    ctx.fillStyle = color;
    ctx.fillRect(x1 + text_pad - 1, y1 - parseInt(text_size * 0.5) - 1, text_width + 2, text_size + 1);
    ctx.fillStyle = GetContrastTextColor(color);
    ctx.fillText(text, x1 + text_pad, y1 + parseInt(text_size * 0.3), text_width);
  }

  /* Making some areas blocked until necessary action done */
  function blockInput(activate = true) {
    imageGettingProcessed = activate;
    if (activate) {
      $('.block-input').removeClass('hidden');
    } else {
      $('.block-input').not('.hidden').addClass('hidden');
    }
  }
});
