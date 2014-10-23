
$('#delete-entry').click(function(ev) {
	if (confirm('Are you sure you want to delete this entry?')){
		$('#action').val('delete');
	} else {
		ev.preventDefault();
	}
});

$('.post-images').on('click', '.delete-img', function(ev) {
	ev.preventDefault();
	var div = $(ev.target).parent();
	if (confirm('Are you sure you want to delete this photo?')){
		$.post('/image/delete/' + $(this).data('img'), function(result) {
			$(div).fadeOut(function() {
				$(div).remove();
			})
		});
	}
});

$('#add-photo-button').click(function(ev) {
	ev.preventDefault();
	$('#transparent-background, .dialog').fadeIn(200);
});



function uploadProgress(e) {
	if (e.lengthComputable) {
		var percentComplete = Math.round(e.loaded * 100 / e.total);
		progressMessage('Uploaded ' + percentComplete.toString() + '% of image');
		if (percentComplete == 100) {
			progressMessage('Saving image ...');
		}
	}
	else {
		progressMessage('Unable to calculate progress');
	}
}

function uploadComplete(e) {
	var result = $.parseJSON(e.target.responseText);
	if (result.status == 'ok') {
		$('<div>').html(
			'<a href="/image/:file" target="_blank" class="fullsize-image"><img src="/image/:file" class="thumbnail" /></a><a class="delete-img" href="#delete-image" data-img=":file">Delete</a>'
			.replace(/:file/g, result.filename))
			.appendTo('.post-images');
		$('#transparent-background, .dialog').fadeOut(200, clearUploadForm);
	} else {
		progressMessage(result.message, 'red');
	}
}

function clearUploadForm() {
	progressMessage('&nbsp;');
	$('#fileform').get(0).reset();
	$('#upload-photo-button').attr('disabled', 'disabled');	
}

function uploadFailed(e) {
 	progressMessage('Upload failed!', 'red');
}

function uploadCanceled(e) {
 	progressMessage('Upload cancelled!', 'red');
}

$('#cancel-add-photo-button').click(function() {
	$('#transparent-background, .dialog').fadeOut(200, clearUploadForm);
});	

function progressMessage(msg, color) {
	$('#upload-photo-progress').html(msg).css('color', color || 'black');
}

$('#photo').change(function() {
	var filename = $(this).val();
	if (filename.match(/\.(jpe?g|png|bmp|gif)$/i)) {
		$('#upload-photo-button').removeAttr('disabled');
	} else {
		$('#upload-photo-button').attr('disabled', 'disabled');
		progressMessage('File must end with .jpg, .png, .gif or .bmp', 'red');
	}
});

$('#upload-photo-button').click(function(ev) {
	ev.preventDefault();
	$('#upload-photo-button').attr('disabled', 'disabled');
	$.get('/api/photouploadurl', function(data) {
		var xhr = new XMLHttpRequest();
		var form = new FormData();
		form.append("photo", document.getElementById('photo').files[0]); 
		form.append("year", $('#year').val());
		form.append("month", $('#month').val());
		form.append("day", $('#day').val());

		xhr.upload.addEventListener("progress", uploadProgress, false);
		xhr.addEventListener("load", uploadComplete, false);
		xhr.addEventListener("error", uploadFailed, false);
		xhr.addEventListener("abort", uploadCanceled, false);
		xhr.open("POST", data.upload_url);
		xhr.send(form);
	});
});
