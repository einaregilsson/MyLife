

$('#export-entries').click(function() {
	disableAll();
	$.post('/export/start', function(data) {
		$('#export-progress').html(data.message);
		var id = data.id;

		function getStatus() {
			$.getJSON('/export/status/' + id, function(result) {
				$('#export-progress').html(result.message);
				if (result.status == 'finished'){
					$('#export-progress').html('Export finished. <a href="/export/download/' + result.filename + '">Download ' + result.filename + '</a>');
					$('#delete-message').show();
					enableAll();
				} else if (result.status == 'failed') {
					$('#export-progress').css('color', 'red').html(result.message);
					enableAll();
				} else {
					setTimeout(getStatus, 1000);
				}
			});
		}
		getStatus();
	});
});


function disableAll() {

	$('input, button, select').attr('disabled', 'disabled');
}

function enableAll() {
	$('input, button, select').removeAttr('disabled');
	$('#import-form').get(0).reset();
	$('#upload').attr('disabled', 'disabled');
}

function uploadFile(e) {
	e.preventDefault();
	var name = $('#zip').val();

	disableAll();
	var xhr = new XMLHttpRequest();
	var data = new FormData();
	data.append("zip", document.getElementById('zip').files[0]); 

	/* event listners */
	xhr.upload.addEventListener("progress", uploadProgress, false);
	xhr.addEventListener("load", uploadComplete, false);
	xhr.addEventListener("error", uploadFailed, false);
	xhr.addEventListener("abort", uploadCanceled, false);
	url = $('#upload').data('upload-url');
	xhr.open("POST", url);
	xhr.send(data);
}

function uploadProgress(e) {
  if (e.lengthComputable) {
    var percentComplete = Math.round(e.loaded * 100 / e.total);
    $('#import-progress').html('Uploaded ' + percentComplete.toString() + '% of zip file');
  }
  else {
    $('#import-progress').html('Unable to calculate progress');
  }
}

function uploadComplete(e) {
  var result = $.parseJSON(e.target.responseText);
  $('#import-progress').html(result.message);
  var taskId = result.id;
  var interval = 1000;

  function getStatus() {
    $.getJSON('/import/status/' + taskId, function(data) {
      
      if (data.status == 'failed') {
        $('#import-progress').css('color', 'red').html(data.message);
        enableAll();
      } else if (data.status == 'inprogress') {
        $('#import-progress').html(data.message);
        setTimeout(getStatus, interval);
      } else if (data.status == 'finished') {
        $('#import-progress').html(data.message);
        enableAll();
      } else if (data.status == 'new') {
        $('#import-progress').html('Waiting for import to start...');
        setTimeout(getStatus, interval);
      }

    });
  }

  getStatus();
}


function uploadFailed(e) {
  $('#import-progress').css('color', 'red').html('Upload failed!')
}

function uploadCanceled(e) {
  $('#import-progress').css('color', 'red').html('Upload cancelled!')
}

$('#upload').click(uploadFile);
$('#zip').change(function() {
	var name = $(this).val();
	if (name && name.match(/\.zip$/i)) {
		$('#upload').removeAttr('disabled');
		$('#import-progress').css('color', 'black').html('Ready to start import');
	} else {
		$('#upload').attr('disabled', 'disabled');
	 	$('#import-progress').css('color', 'red').html('You can only upload .zip files');
	}
});





// Migration of images to Google Cloud Storage

function migrateToGcs() {
	disableAll();
	$.post('/migrate/start', function(data) {
		$('#migrate-progress').html(data.message);
		var id = data.id;

		function getStatus() {
			$.getJSON('/migrate/status/' + id, function(result) {
				if (result.status == 'finished'){
					$('#migrate-progress').html(result.message);
					enableAll();
					$('#migrate-to-gcs').attr('disabled', 'disabled');
				} else if (result.status == 'failed') {
					$('#migrate-progress').css('color', 'red').html(result.message);
					enableAll();
				} else {
					if (result.message) {
						$('#migrate-progress').html(result.message);
					}
					setTimeout(getStatus, 1000);
				}
			});
		}
		getStatus();
	});	
}

$('#migrate-to-gcs').click(migrateToGcs);

