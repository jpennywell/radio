$(document).ready(function() {

	function save_option(o_name, o_val) {
		$.ajax({
			cache: false,
			url: '/ajax/save_option',
			type: 'GET',
			content-type: 'application/json',
			dataType: 'json',
			data: JSON.stringify({'name': o_name, 'value': o_val})
		}).done(function(json) {
			$(o_name).addClass('has-success');
			setTimeout(function() {
				$(o_name).removeClass('has-success');
			}, 3000);
		}).error(function(json) {
			$(o_name).addClass('has-error');
			setTimeout(function() {
				$(o_name).removeClass('has-error');
			}, 3000);
		});
	}

	$( "form[name='option_form'] > :text" ).each(function() {
		$(this).change(function() {
			save_option(this.attr('name'), this.val());
		}
	});

});
