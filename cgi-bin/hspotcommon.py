#!/usr/bin/python

# Functions contained in this module
#
#	getDpsk() - retrieve DPSK from the ZoneDirector
#	displayWelcome() - a simple welcome web page
#	gotoUrl() - redirect client to a URL
#	setQueryParameter() - add/change a query string parameter
#	downloadProv2server() - download Zero-IT script to the captive portal
#	writeProv2serverFile() - save Zero-IT script
#	createDpsk() - create a new DPSK on the ZD
# 


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
from time import gmtime, strftime


# Custom modules - these must be placed in the same directory as this file
import xmlcommon
  
'''
This script is placed in the the cgi-bin directory of the web server. 

'''


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
  print "Content-type: text/html\n"
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
  <p>To access the network, you must reconfigure your client device to use the secure Wi-Fi network.</p><p> You may either configure the device manually or download a script to automatically provision this device for you.</p><br>
  <div id="dpsk" style="width:420px;height:150px;border:6px double #99CC00;">
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
  "> here </a> to download the auto-configuration tool.</p>
  </center>
  </body>
  </html>
  '''

####################################################################    
# gotoUrl() - go to a specific web URL
#
# args:
#	url - requested URL
#
# returns: none
#################################################################### 
def gotoUrl(url):

  # Construct a small HTML page that redirects to the requested URL
  print ('<html><head><meta HTTP-EQUIV="REFRESH" content="0; url=' + url + '">' + '</head></body></html>')

  sys.exit(1)

####################################################################
# setQueryParameter() - set or replace a query string parameter
#
# args:
#       url = original URL
#       param_name = parameter name
#       param_value = parameter value
#
# returns: new_url
####################################################################
def setQueryParameter(url, param_name, param_value):
  scheme, netloc, path, query_string, fragment = urlsplit(url)
  query_params = parse_qs(query_string)

  query_params[param_name] = [param_value]
  new_query_string = urlencode(query_params, doseq=True)

  new_url = urlunsplit((scheme, netloc, path, new_query_string, fragment))

  return new_url

####################################################################
# downloadProv2server() - download the Zero-IT file to the web server
# 
# args:
#       nbi_password = northbound interface password
#	nbi_url = northbound interface URL
#	client_ip = client IP address
#       client_mac = client MAC
#	username = login username
#       wlan = SSID name
#	expiration = expiration time
#	key_length = length of D-PSK in bytes
#	vlan = VLAN ID
#
# returns: prov_url
####################################################################
def downloadProv2server(nbi_password, nbi_url, client_ip, client_mac, username, wlan, expiration, key_length, vlan):

  # Generate the XML request
  xml_request, ext = xmlcommon.createXmlFetchProv(nbi_password, nbi_url, client_ip, client_mac, username, wlan, expiration, key_length, vlan)

  # Send the request to the ZD and capture response. The response is in XML format
  xml_response =  xmlcommon.sendXmlString(xml_request, nbi_url)

  # The response can be a binary stream or an XML file with a return code
  # File download location is hard-coded here to /downloads
  tmpdt = strftime('%Y%m%d-%H%M%S', gmtime())
  file_loc = 'replace_file_location/prov-%s.%s' % (tmpdt, ext)
  file = 'prov-%s.%s' % (tmpdt, ext)

  # This should be changed to match the root directory for your web files
  server_loc = '/var/www/'

  # Parse the response
  msgData = xmlcommon.getXmlTagData(xml_response, 'response-code')

  if msgData:
	print "Content-type: text/html \n\n"
        print "get prov failed with code %s" % msgData
        file_loc = file_loc.replace('.exe', '.xml')

  server_loc += file_loc
  writeProv2serverFile(xml_response, server_loc)

  # Construct the full HTTP URL for prov.exe
  server = os.environ["SERVER_NAME"]
  prov_url = 'http://' + server + file_loc
  
  return prov_url


####################################################################
# writeProv2serverFile() - download the Zero-IT file to the server
#
# args:
#       stream = download file
#       file_loc = file location
#
# returns: none
####################################################################
def writeProv2serverFile(stream, file_loc):

  # Write the file
  with open(file_loc, 'wb') as fp:
	fp.write(stream)

  return

####################################################################
# getProvLink() - get the URL to allow the client to download Zero-IT
#
# args:
#       nbi_password = northbound interface password
#       prov_url = Request URL for prov file
#       client_mac = client MAC
#       wlan = SSID name
#
# returns: post_response
####################################################################
def getProvLink(nbi_password, prov_url, client_mac, wlan):

  # Create the client string to hash
  client_string = ''
  client_string += client_mac + "&" + wlan + "&" + nbi_password

  # Create a SHA1 hash using the client information
  m = hashlib.sha1()
  m.update(client_string)
  key = m.hexdigest()
  key = urllib.unquote(key)
  
  req_url = ''
  req_url += prov_url + "?"
  req_url += "mac=" + client_mac + "&"
  req_url += "wlan=" + wlan + "&"
  req_url += "key=" + key
  
  return req_url

####################################################################
# downloadProv2client() - download Zero-IT script to client
#
# args:
#       prov_url = Request URL for prov file
#
# returns: none
####################################################################
def downloadProv2client(prov_url):

  # Construct a small HTML page that redirects to the download URL
  print ('<html><head><meta HTTP-EQUIV="REFRESH" content="0; url=' + prov_url + '">' + '</head></body></html>')

  return True

####################################################################
# createDpsk() - create a D-PSK for the user
#
# args:
#       nbi_password - northbound interface password for ZoneDirector
#       nbi_url = URL for northbound interface on ZD
#       client_ip = client IP address
#       client_mac = client MAC
#       username = client username
#       password = client password
#       expiration_time = key expiration in hours
#       key_length = length of generated key
#       wlan = SSID name for secure network
#       vlan = VLAN ID
#	restricted = True or False
#
# returns: success
####################################################################
def createDpsk(nbi_password, nbi_url, client_ip, client_mac, username, password, expiration, key_length, wlan, vlan, restricted):

  # Create XML string to generate a DPSK for the user
  xml_request = xmlcommon.createXmlDpskReq(nbi_password, client_ip, client_mac, username, password, expiration, key_length, wlan, vlan, restricted)

  # Send the request to the ZD and capture response. The response is in XML format
  xml_response =  xmlcommon.sendXmlString(xml_request, nbi_url)

  # Check response
  success = False
  if not xml_response:
        print "Content-type: text/html \n\n"
        print "DPSK generation failed: No response from ZoneDirector"
  else:
        response_code = xmlcommon.checkXmlResponse(xml_response)
        # Lookup the code returned to see if it indicates successful authentication
        success = xmlcommon.statusCodeLookup(response_code, "dpsk")

  return success

