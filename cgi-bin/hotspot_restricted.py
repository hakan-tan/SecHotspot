#!/usr/bin/python

from subprocess import Popen
from xml.dom import minidom
import cgi     
import cStringIO
import os
import pycurl  
import re
import socket
import logging
import urllib
import urllib2
from urlparse import parse_qs, urlsplit, urlunsplit
from urllib import urlencode
import hashlib
import sys


# Custom modules - these must be placed in the same directory as this file
import xmlcommon
import hspotcommon
  
'''
This script is placed in the the cgi-bin directory of the web server. 

The flow of this program is as follows:
1. Pull in username, password, etc. from login form 
2. Create  an XML authentication request string and send to ZoneDirector (ZD)
3. Based on ZD return code - direct to relevant html page
	authentication success -> go to originally requested URL
	authentication failed -> go to login page
4. Generate a D-PSK for the suer on the ZD
'''

####################################################################
# main() - start here
#		Northbound Interface password is coded here!
####################################################################
def main(): 
    
  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  # Northbound interface password
  # Change this to match the password configured on the ZoneDirector
  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  nbi_password = 'hakantan'  
 
  # D-PSK information
  # Expiration time is in hours, key length is number of characters in the generated D-PSK
  expiration_time = '1'
  key_length  = '6'

  # Need some required values from the form: username, password, client IP, client MAC
  # These should have been stored as hidden fields in the form by Javascript
  form = cgi.FieldStorage()

  # User name
  tmp_username = form["username"].value
  if len(tmp_username) == 0:
    return
  username = tmp_username.strip()

  # User password
  tmp_password = form["password"].value
  if len(tmp_password) == 0:
    return 
  password = tmp_password.strip()
  
  # ZoneDirector IP address
  tmp_zip = form["zip"].value
  if len(tmp_zip) == 0:
    return 
  zd_ip = tmp_zip.strip()

  # Client device IP address
  tmp_uip = form["uip"].value
  if len(tmp_uip) == 0:
    return 
  client_ip = tmp_uip.strip()
  
  # Client device MAC
  tmp_cmac = form["client_mac"].value
  if len(tmp_cmac) == 0:
    return 
  foo = tmp_cmac.strip()

  # Convert MAC address to xx:xx:xx:xx:xx:xx format. ZD only passes as a string of 6 octets, e.g. a0b0c0c0eef0
  client_mac = re.sub(r'(.{2})(?!$)', r'\1:', foo)

  # The URL originally requested by the client browser
  tmp_requested_url = form["requested_url"].value
  if len(tmp_requested_url) == 0:
    return 
  requested_url = tmp_requested_url.strip()

  # The login page user is redirected to if authentication fails. This should be the referrer URL (redirect) 
  # the ZD originally sent to the client since the query string is needed to start the process again
  tmp_login_url = form["login_url"].value
  if len(tmp_login_url) == 0:
    return 
  login_url = tmp_login_url.strip()

  # SSID name
  # All users sent to the SSID 'hotspot-secure' for DPSK. Change this to use a different WLAN
  wlan = "hakanSSID"

  # VLAN ID
  tmp_vlan = form["vlan"].value
  if len(tmp_vlan) == 0:
    return 
  vlan = tmp_vlan.strip()

  # nbi_url is the URL for the northbound interface of the ZD. If using a different HTTPS port, this must be
  # changed below
  nbi_url = ''
  nbi_url += "https://" + zd_ip + ":443/admin/_portalintf.jsp"

  # prov_url is the URL to provison a Zero-IT script
  prov_url = "https://" + zd_ip + "/user/user_extern_prov.jsp"

  # Authentication Request ##################
  success = ''
  success = authenticateUser(nbi_password, nbi_url, client_ip, client_mac, username, password)

  # If authentication was not successful, set the "login_result" parameter in the query string = "failed"
  if not success:
        redirect_url = hspotcommon.setQueryParameter(login_url, "login_result", "failed")
	# Go back to login page
        hspotcommon.gotoUrl(redirect_url)

  # If successful, set login_result to "success" and go on to request a D-PSK for the user
  q = hspotcommon.setQueryParameter(login_url, "login_result", "success")

  # DPSK Request ##################
  # Note: the details of the key are returned by the ZD as part of its 
  # response to the key generation request
  # Therefore a second call is not strictly necessary
  success = False
  restricted = True
  success = hspotcommon.createDpsk(nbi_password,nbi_url, client_ip, client_mac, username, password, expiration_time, key_length, wlan, vlan, restricted)

  # If the ZD did not respond indicating successful generation set the "dpsk_result" parameter in the query string
  # to "failed"
  if not success:
        q = hspotcommon.setQueryParameter(login_url, "dpsk_result", "failed")
        hspotcommon.gotoUrl(login_url)

  # Otherwise, set the dpsk_result to "created" and go on to retrieve the value
  q = hspotcommon.setQueryParameter(login_url, "dpsk_result", "created")

  # Retrieve DPSK ##################
  passphrase = ''
  passphrase, expiration_date = hspotcommon.getDpsk(nbi_password, nbi_url, client_mac, wlan)

  # If the ZD did not respond indicating successful generation , set the "dpsk_result" parameter in the query string
  # to "failed"
  if not success:
        q = hspotcommon.setQueryParameter(login_url, "dpsk_result", "failed")
        hspotcommon.gotoUrl(login_url)

  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  # You have a choice here - download the provisioning script to the web
  # server and then serve it to the client or allow the client to download
  # it directly from the ZD
  # Uncomment the code below for the choice you prefer
  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

  prov_link = ''
  # Download Zero-IT to server ##################
  prov_link = ''
  prov_link = hspotcommon.downloadProv2server(nbi_password, nbi_url, client_ip, client_mac, username, wlan, expiration_time, key_length, vlan)
 
  # Get Zero-IT link for client ##################
#  prov_link = hspotcommon.getProvLink(nbi_password, prov_url, client_mac, wlan)

  # Didn't get the prov.exe file. Getting this file does not affect if the client 
  # is authorized or not, so the choice of action is up to you. 
  if not prov_link:
        print "Content-type: text/html \n\n"
        print "get prov failed"

  # Display the welcome page with D-PSK information
  hspotcommon.displayWelcome(nbi_password, prov_link, client_mac, passphrase, expiration_date, wlan)

  return True


####################################################################    
# authenticateUser() - user authentication to ZD
#
# args:
#	nbi_password - northbound interface password for ZoneDirector
#	nbi_url = URL for northbound interface on ZD
#	client_ip = client IP address
#	client_mac = client MAC
#	username = client username
#	password = client password
#
# returns: success
#################################################################### 
def authenticateUser(nbi_password,nbi_url,client_ip,client_mac,username,password):

  # Create the XML authentication request 
  xml_request = xmlcommon.createXmlAuthReq(nbi_password,client_ip,client_mac,username,password)

  # Send the XML authentication request to the ZD and capture response. The response is in XML format
  xml_response =  xmlcommon.sendXmlString(xml_request,nbi_url)

  # Check response
  success = ''
  if not xml_response:
   	print "Content-type: text/html \n\n"
        print "Authentication request failed: No response from ZoneDirector."
	return 
  else:
        response_code = xmlcommon.checkXmlResponse(xml_response)
        # Lookup the code returned to see if it indicates successful authentication
        success = xmlcommon.statusCodeLookup(response_code, "auth")

  return success




####################################################################    
# getDpsk() - retrieve the D-PSK for the user
#
# args:
#	nbi_password - northbound interface password for ZoneDirector
#	nbi_url = URL for northbound interface on ZD
#	client_mac = client MAC
#	wlan = SSID name for secure network
#
# returns:
#	passphrase = D-PSK 
#	expiration = key expiration
#################################################################### 
def getDpsk(nbi_password, nbi_url, client_mac, wlan):

 # Create XML string to retrieve the newly created DPSK for the user
  xml_request = xmlcommon.createXmlFetchDpsk(nbi_password, client_mac, wlan)

  # Send the request to the ZD and capture response. The response is in XML format
  xml_response =  xmlcommon.sendXmlString(xml_request, nbi_url)

  # Check response
  success = False
  if not xml_response:
  	print "Content-type: text/html \n\n"
        print "Retrieve DPSK failed: No response from ZoneDirector"
  else:
        response_code = xmlcommon.checkXmlResponse(xml_response)
        # Lookup the code returned to see if it indicates successful authentication
        success = xmlcommon.statusCodeLookup(response_code, "dpsk")

  if not success:
	return False

  passphrase = xmlcommon.getXmlAttribute(xml_response,"dpsk","passphrase")
  expiration = xmlcommon.getXmlAttribute(xml_response,"dpsk","expiration")

  return passphrase, expiration


####################################################################
# displayWelcome() - display welcome page with D-PSK configuration
#
# args:
#	nbi_password = northbound interface password
#	prov_link = Zero-IT provisioning URL
#	client_mac = client MAC
#       passphrase = D-PSK
#       expiration = expiration date
#       wlan = SSID name for secure network
#
# returns: none
####################################################################
def displayWelcome(nbi_password, prov_link, client_mac, passphrase, expiration, wlan):
  print "Content-type: text/html \n\n"
  print '''
  <html>
  <title>Welcome to the public Wi-Fi network</title>
  <body>
  <center>
  <p align=center>
  <img src="../images/RuckusLogo.jpg" width=300 align="left">
  <br><br><br> <br><br><br> <br><br><br> <br><br><br> <br><br><br>
  <h2>Authentication Successful!</h2>
  <br>
  <p>To access the network, you must reconfigure your client device to use the secure Wi-Fi network. You can either configure the device manually or download a script to automatically provision this device for you.</p><br>
  <div id="dpsk" style="background-color:gold;width:420px;height:150px;border:6px double orange;">
  <table border="0" width="400">
  <tr></tr>
  <tr>
    <td width="200">SSID Name:</td>
    <td><b>
  '''
  print wlan
  print '''
  </b></td>
  </tr>
  <tr>
  <td> Passphrase:</td>
  <td><b>
  '''
  print passphrase
  print '''
  </b></td>
  </tr>
  <tr>
  <td>Encryption:</td>
  <td><b>WPA2 Personal (PSK)</b></td>
  </tr>
  </table>
  <br>
  <p>Access is granted until <b>
  ''' 
  print expiration
  print '''
  </b>
  </div id="dpsk">
  <br>
  <p>Click <a href="
  '''
  print prov_link
  print '''
  print "> here </a> to download the auto-configuration tool.</p>
  </center>
  </body>
  </html>
  '''


if __name__ == "__main__": main() 

