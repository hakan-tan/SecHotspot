// get_param - parse a query string for a parameter value
// 
// args:
//	name = URL or query string
//
// returns:value or emptry string "" if parameter is not present
function get_param(name) {
    if (location.href.indexOf("?") >= 0) { 
        var query=location.href.split("?")[1];
        var params=query.split("&");
        for (var i=0; i < params.length; i ++) {
            value_pair=params[i].split("=");
            if (value_pair[0] == name)
                return unescape(value_pair[1]);
        }
    }
    return "";
}

// hotspot_unrestricted_form_check - check form information (called before submit)
// 
// args:
//	form = form to check
//
// returns: true (all required fields are present) or false
function hotspot_unrestricted_form_check(form) {
  // Username is required
  if (form.username.value == "") {
    alert( "Please enter your email address: " );
    return false ;
  }
  return true ;
}

// hotspot_login_form_check - check form information (called before submit)
// 
// args:
//	form = form to check
//
// returns: true (all required fields are present) or false
function hotspot_login_form_check(form) {
  // Username and password are required
  if (form.username.value == "") {
    alert( "Please enter your user name: " );
    return false ;
  }
  if (form.password.value == "") {
    alert( "Please enter your password." );
    return false ;
  }
  return true ;
}

// hotspot_login_form - output hotspot login form
//
// args: none
//
// user-supplied fields:
//	username = login name
//	temp_password = password
//
// hidden fields: 
//	ap_mac = AP MAC
//	zip = ZD IP address
//	client_mac = client MAC
//	uip = client IP address
//	requested_url = URL requested by user
//	login_url = the URL of this page
//	ssid = WLAN name
//	vlan = VLAN ID
//	login_mode = restricted or unrestricted mode
//
// on submit: call hotspot_login_form_check
function hotspot_login_form() {
    document.write('<form name="hotspot_login_form" method="post"');
    document.write('action="../cgi-bin/hotspot_login.py"');
    document.write('onsubmit="return hotspot_login_form_check(this.form"');

// Hidden form fields
    document.write('<input type="hidden" name="ap_mac" value="' + get_param('mac') + '">\n');
    document.write('<input type="hidden" name="zip" value="' + get_param('sip') + '">\n');
    document.write('<input type="hidden" name="client_mac" value="' + get_param('client_mac') + '">\n');
    document.write('<input type="hidden" name="uip" value="' + get_param('uip') + '">\n');
    document.write('<input type="hidden" name="requested_url" value="' + get_param('url') + '">\n');
    document.write('<input type="hidden" name="login_url" value="' + window.location.href + '">\n');
    document.write('<input type="hidden" name="ssid" value="' + get_param('ssid') + '">\n');
    document.write('<input type="hidden" name="vlan" value="' + get_param('vlan') + '">\n');
    document.write('<input type="hidden" name="login_mode" value="restricted">\n');
 
}

// hotspot_unrestricted_form - output hotspot form for unrestricted users
//
// args: none
//
// user-supplied fields:
//	temp_password = password
//
// hidden fields: 
//	ap_mac = AP MAC
//	zip = ZD IP address
//	client_mac = client MAC
//	uip = client IP address
//	requested_url = URL requested by user
//	login_url = the URL of this page
//	ssid = WLAN name
//	vlan = VLAN ID
//	login_mode = restricted or unrestricted
//
// on submit: call hotspot_unrestricted_form_check
function hotspot_unrestricted_form() {
    document.write('<form name="hotspot_unrestricted_form" method="post"');
    document.write('action="../cgi-bin/hotspot_login.py"');
    document.write('onsubmit="return hotspot_unrestricted_form_check(this.form"');

// Hidden form fields
    document.write('<input type="hidden" name="ap_mac" value="' + get_param('mac') + '">\n');
    document.write('<input type="hidden" name="zip" value="' + get_param('sip') + '">\n');
    document.write('<input type="hidden" name="client_mac" value="' + get_param('client_mac') + '">\n');
    document.write('<input type="hidden" name="uip" value="' + get_param('uip') + '">\n');
    document.write('<input type="hidden" name="requested_url" value="' + get_param('url') + '">\n');
    document.write('<input type="hidden" name="login_url" value="' + window.location.href + '">\n');
    document.write('<input type="hidden" name="ssid" value="' + get_param('ssid') + '">\n');
    document.write('<input type="hidden" name="vlan" value="' + get_param('vlan') + '">\n');
    document.write('<input type="hidden" name="login_mode" value="unrestricted">\n');
 
}

// update_display() - refresh page
//
// args: none
//
// returns: none
function update_display()
{
    var res = get_param("login_result");
    var display = {"login":"none", "logoff":"none", "status":"none"};

    if (res == "success" ) {
        display["status"] = "block";
    } else if (res == "logoff") {
        display["logoff"] = "block";
    } else if (res == "notyet" || res == "failed") {
        display["login"] = "block";
    }

    for (d in display) {
        document.getElementById(d).style.display = display[d];
    }
}

// message() - print a message to the screen
//
// args: no explicit args, fetches value from referrer URL
//
// returns: none
function message() {
  var msgStr = "";


    var login_result = get_param("login_result");
    if (login_result == "failed") {
        msgStr = "Login failed. Please try again."
    }
  document.write(msgStr.fontcolor("red"));
}

