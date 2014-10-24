$(document).ready(function() {

	var date = new Date();

	displayDate(date);

	$('a[href="#prev-month"]').click(function(ev) {
		ev.preventDefault();
		date = new Date(date.getFullYear(), date.getMonth()-1, 1);
		displayDate(date);
	});
	$('a[href="#next-month"]').click(function(ev) {
		ev.preventDefault();
		var today = new Date();
		if (today.getMonth() == date.getMonth() && today.getFullYear() == date.getFullYear()) {
			return;
		}
		date = new Date(date.getFullYear(), date.getMonth()+1, 1);
		displayDate(date);
	});

});

var dateCache = {};

var currentDateKey, currentOffset, currentDaysInMonth;

function displayDate(date) {
	var months = ["January", "February", "March", "April", "May", "June",
					"July", "August", "September", "October", "November", "December"];


	var month = months[date.getMonth()];

	$('.month-name').text(month + ' ' + date.getFullYear());

	var firstOfMonth = new Date(date.getFullYear(), date.getMonth(), 1);
	var offset = firstOfMonth.getDay();

	var days = daysInMonth(date)
	var today = new Date();
	var isCurrentMonth = today.getFullYear() == date.getFullYear() && today.getMonth() == date.getMonth();
	if (isCurrentMonth) {
		$('a[href="#next-month"]').addClass('disabled');
	} else {
		$('a[href="#next-month"]').removeClass('disabled');
	}
	
	$('td div').text('');
	for (var i = 1; i <= days; i++) {
		var id = '.d' + (i+offset) + ' div';
		if (isCurrentMonth && i > today.getDate()) {
			$(id).html(i);
		} else {
			$(id).html('<a href="/write/' + date.getFullYear() + '-' + zpad(date.getMonth()+1) + '-' + zpad(i) + '">' + i + '</a>');
		}
	}

	if (days + offset >= 36) { //Ugly to have empty last line
		$('#lastline').show();
	} else {
		$('#lastline').hide();
	}

	var dateKey = (date.getFullYear() + '-' + (date.getMonth()+1)).replace(/-(\d)$/, '-0$1');
	currentDateKey = dateKey;
	currentOffset = offset;
	currentDaysInMonth = days;

	if (dateCache[dateKey]) {
		addCheckMarks(dateKey, dateCache[dateKey])
	} else {
		$.get('/postdates/' + dateKey, function(data) {
			dateCache[dateKey] = data.days;
			addCheckMarks(data.key, data.days);
		});
	}

}

function addCheckMarks(key, days) {
	if (key != currentDateKey) {
		return;
	}
	for (var i = 0; i < days.length; i++) {
		var day = days[i];
		var id = '.d' + (day+currentOffset) + ' div';
		$(id).append($('<span>&#x2713;</span>'));
	}	
}
function zpad(d) {
	return d < 10 ? '0'+d : d+'';
}
function daysInMonth(date) {
	var y = date.getFullYear(), m = date.getMonth();
	var isLeapYear = ((y % 4 == 0) && (y % 100 != 0)) || (y % 400 == 0);
	return [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m];
}