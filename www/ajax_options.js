$(document).ready(function() {
	function save_option() {
		$.ajax({
			cache: false,
			url: '/ajax/save_option',
			type: 'GET',
			content-type: 'application/json',
			dataType: 'json',
			data: JSON.stringify({'input': $(option_name).val()})
		}).done(function(json) {
			$(option_name).addClass('success');
		}).error(function(json) {
			$(option_name).addClass('error');
		});
	}

	$(option_name).change(function() {
		save_option();
	});
});
