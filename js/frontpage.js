
$(document).ready(function() {
	$('#content').on('click', '.find-post a', function(ev) {
		ev.preventDefault();
		var url = $(this).data('url');
		$('#content').load(url);
	})
});