## Need to make this function work for every <input> box.

$(document).ready(function() {
	function save_option(o_name, o_val) {
		$.ajax({
			cache: false,
			url: '/ajax/save_option',
			type: 'GET',
			content-type: 'application/json',
			dataType: 'json',
			data: JSON.stringify({'input': o_val})
		}).done(function(json) {
			$(o_name).addClass('success');
		}).error(function(json) {
			$(o_name).addClass('error');
		});
	}

	$( "form[name='option_form'] > :text" ).each(function() {
		$(this).change(function() {
			save_option(this.attr('name'), this.val());
		}
	});
});
