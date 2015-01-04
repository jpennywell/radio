$(document).ready(function() {
	function save_option(o_name, o_val) {
		elt = 'input[name=' + o_name + ']'
		$.ajax({
			cache: false,
			url: '/ajax_save_option',
			type: 'POST',
			contentType: 'application/json',
			data: JSON.stringify({'table': 'options', 'name': o_name, 'value': o_val}),
			dataType: 'text',
			success: function(json) {
				$(elt).css('color', 'blue')
				setTimeout(function() {
					$(elt).css('color', 'black');
				}, 3000);
			},
			error: function(json) {
				alert(JSON.stringify(json))
				$(o_name).css('color', 'red');
				setTimeout(function() {
					$(o_name).css('color', 'black');
				}, 3000);
			}
		});
	}

	$( "form[name='option_form'] :text" ).each(function() {
		$(this).change(function() {
			save_option($(this).attr('name'), $(this).val());
		});
	});

});
