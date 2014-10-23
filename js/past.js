$(document).ready(function() {
	$('#archive').change(function() {
		var val = $(this).val();

		location.href = '/past/' + val;
	});
});