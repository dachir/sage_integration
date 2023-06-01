// Copyright (c) 2023, Richard and contributors
// For license information, please see license.txt

const getLocation = (frm) =>{
	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function(position) {
		  const latitude = position.coords.latitude;
		  const longitude = position.coords.longitude;
	
		  // Set the values of the latitude and longitude fields on the form
		  if(!frm.doc.latitude) frm.set_value('latitude', latitude);
		  if(!frm.doc.longitude) frm.set_value('longitude', longitude);
		});
	} 
	else {
		frappe.msgprint(__('Geolocation is not supported by this browser.'));
	}
}

frappe.ui.form.on('Boulangerie', {  
	refresh: function(frm) {
		// Add a button to the form to retrieve the location
		if(frm.is_new()) {
			getLocation(frm);
			frm.set_value('enqueteur', frappe.session.user);
		}

		frm.add_custom_button(
			__("Localisation"),
			function () {
				getLocation(cur_frm);
			},
		);

	},
});
