#!/usr/bin/python

# Functions contained in this module
#
# 	createXmlAuthReq() - construct an XML string for user authentication to the ZD 
#	createXmlUnrestrictedUser() - construct an XML string to create an unrestricted user
#	createXmlDpskReq() - construct an XML string for DPSK generation to the ZD
#	createXmlUnrestrictedDpskReq() - construct an XML string for DPSK generation to the ZD
#	createXmlFetchDpsk() - construct an XML string to retreive a DPSK from the ZD
# 	createXmlFetchProv() - construct an XML string to retreive a Zero-IT script from the ZD
#	sendXmlString() - Send the xml string to the ZD and pickup the return string
#	checkXmlResponse() - check response status code
#	getXmlAttribute() - extract a value from the ZD response by tag name
#	statusCodeLookup() - check returned request code from ZD
# 
# Globals
#	class authReqCodes
# 	authRespCodeList[]
#	dpskRespCodeList[]

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

##########################################################################################
# createXmlAuthReq() - construct an XML string for user authentication to the ZD
#
# args: 
#	nbi_password = northbound interface password must match password configured on ZD
#	client_ip = client IP address
#	client_mac = client MAC
#	username = user login name
#	password = user login password
#
# returns: xml_request 
##########################################################################################
def createXmlAuthReq(nbi_password,client_ip,client_mac, username, password):
     
    xml_list = ['<ruckus><req-password>']
    xml_list.append(nbi_password)
    xml_list.append('</req-password>')
    xml_list.append('<version>1.0')
    xml_list.append('</version>')
    xml_list.append('<command cmd= "user-authenticate"')
    xml_list.append(' ipaddr="')
    xml_list.append(client_ip)
    xml_list.append('"')
    xml_list.append(' macaddr="')
    xml_list.append(client_mac)
    xml_list.append('"')
    xml_list.append(' name="')
    xml_list.append(username),
    xml_list.append('" ')
    xml_list.append(' password="')
    xml_list.append(password)
    xml_list.append('"/> </ruckus>')
    xml_request =  "".join(xml_list)
    xmlTrimedString = xml_request
    
    return xml_request


##########################################################################################
# createXmlUnrestrictedUserReq() - construct an XML string for an unrestricted user
#
# args: 
#	nbi_password = northbound interface password must match password configured on ZD
#	client_ip = client IP address
#	client_mac = client MAC
#	username = user login name
#
# returns: xml_request
##########################################################################################
def createXmlUnrestrictedUserReq(nbi_password, client_ip, client_mac, username):

  xml_list = ['<ruckus><req-password>']
  xml_list.append(nbi_password)
  xml_list.append('</req-password>')
  xml_list.append('<version>1.0')
  xml_list.append('</version>')
  xml_list.append('<command cmd= "unrestricted" ')
  xml_list.append(' ipaddr="')
  xml_list.append(client_ip)
  xml_list.append('"')
  xml_list.append(' macaddr="')
  xml_list.append(client_mac)
  xml_list.append('"')
  xml_list.append(' name="')
  xml_list.append(username)
  xml_list.append('"')
  xml_list.append('/>')
  xml_list.append('</ruckus>')
  xml_request =  "".join(xml_list)

  return xml_request

##########################################################################################
# createXmlDpskReq() - construct an XML string for DPSK generation to the ZD
#
# args: 
#	nbi_password = northbound interface password must match password configured on ZD
#	client_ip = client IP address
#	client_mac = client MAC
#	username = user login name
#	password = user login password
#	expiration = expiration time
#	key_length = the generated key length
#	wlan = WLAN name
#	vlanId = VLAN ID
#	restricted = True or False
#
# returns: xml_request
##########################################################################################
def createXmlDpskReq(nbi_password, client_ip, client_mac, username, password, expiration, key_length, wlan, vlanId, restricted):
  xml_list = ['<ruckus><req-password>']
  xml_list.append(nbi_password)
  xml_list.append('</req-password>')
  xml_list.append('<version>1.0')
  xml_list.append('</version>')
  xml_list.append('<command cmd= "generate-dpsk">')
  xml_list.append('<dpsk ')
  xml_list.append(' expiration="')
  xml_list.append(expiration)
  xml_list.append('"')
  xml_list.append(' key-length="')
  xml_list.append(key_length)
  xml_list.append('"')
  xml_list.append(' user="')
  xml_list.append(username)
  xml_list.append('"')
  # A password is only required for a restricted user, unrestricted users have no password
  if restricted:
	xml_list.append(' password="')
	xml_list.append(password)
	xml_list.append('"')
  xml_list.append(' mac="')
  xml_list.append(client_mac)
  xml_list.append('"')
  xml_list.append(' vlan-id="')
  xml_list.append(vlanId)
  xml_list.append('"')
  xml_list.append(' wlan="')
  xml_list.append(wlan)
  xml_list.append('"')
  xml_list.append('/>')
  xml_list.append('</command>')
  xml_list.append('</ruckus>')
  xml_request =  "".join(xml_list)

  return xml_request

##########################################################################################
# createXmlFetchDpsk() - construct an XML string to retreive a DPSK from the ZD
#
# args: 
#	nbi_password = northbound interface password must match password configured on ZD
#	client_mac = client MAC
#	username = user login name
#	password = user login password
#	wlan = WLAN name
#
# returns: xml_request
##########################################################################################
def createXmlFetchDpsk(nbi_password, client_mac, wlan):

  xml_list = ['<ruckus><req-password>']
  xml_list.append(nbi_password)
  xml_list.append('</req-password>')
  xml_list.append('<version>1.0')
  xml_list.append('</version>')
  xml_list.append('<command cmd= "get-dpsk">')
  xml_list.append('<dpsk ')
  xml_list.append(' mac="')
  xml_list.append(client_mac)
  xml_list.append('"')
  xml_list.append(' wlan="')
  xml_list.append(wlan)
  xml_list.append('"')
  xml_list.append('/>')
  xml_list.append('</command>')
  xml_list.append('</ruckus>')
  xml_request =  "".join(xml_list)

  return xml_request


##########################################################################################
# createXmlFetchProv() - construct an XML string to retreive a Zero-IT script from the ZD
#
# args: 
#	nbi_password = northbound interface password must match password configured on ZD
#	nbi_url = URL to northbound interface
#	client_ip = client IP address
#	client_mac = client MAC
#	username = user login name
#	wlan = WLAN name
#	expiration = time until expiration of the key (in hours)
#	key_length = length of D-PSK
#	vlan = secure VLAN ID
#
# returns: xml_request, platform
##########################################################################################
def createXmlFetchProv(nbi_password, nbi_url, client_ip, client_mac, username, wlan, expiration, key_length, vlan):

  # Client user agent
  agent = os.environ["HTTP_USER_AGENT"]

  # Length of the agent string cannot be greater than 128 characters
  if len(agent) > 128:
	s = agent[0:128]
	agent = s

  # Find the first matching OS in platformList[]
  platform = ''
  for x in platformList:
	if agent.find(x.agent) != -1:
	  # Found the OS
  	  platform = x.name
	  ext = x.ext

  # Version - only needed for Android
  version = ''
  if platform == "android":
	version = '1.0'

  # Some of these values may not be safe for use in HTTP and need to be encoded to remove unsafe characters
  tmp_username = username
  username = tmp_username

  tmp_wlan = urllib.quote_plus(wlan)
  wlan = tmp_wlan

  tmp_expiration = urllib.quote_plus(expiration)
  expiration = tmp_expiration

  xml_list = ['<ruckus><req-password>']
  xml_list.append(nbi_password)
  xml_list.append('</req-password>')
  xml_list.append('<version>1.0')
  xml_list.append('</version>')
  xml_list.append('<command cmd= "get-prov-file"')
  xml_list.append(' ipaddr="')
  xml_list.append(client_ip)
  xml_list.append('"')
  xml_list.append(' macaddr="')
  xml_list.append(client_mac)
  xml_list.append('"')
  xml_list.append(' username="')
  xml_list.append(username)
  xml_list.append('"')
  xml_list.append(' platform="')
  xml_list.append(platform)
  xml_list.append('"')
  xml_list.append(' user-agent="')
  xml_list.append(agent)
  xml_list.append('"')
  xml_list.append(' version="')
  xml_list.append(version)
  xml_list.append('"')
  xml_list.append('>')
  xml_list.append('<wlansvc name="')
  xml_list.append(wlan)
  xml_list.append('"')
  xml_list.append(' expiration="')
  xml_list.append(expiration)
  xml_list.append('"')
  xml_list.append(' key_length="')
  xml_list.append(key_length)
  xml_list.append('"')
  xml_list.append(' vlan-id="')
  xml_list.append(vlan)
  xml_list.append('"')
  xml_list.append('/>')
  xml_list.append('</command>')
  xml_list.append('</ruckus>')
  xml_request =  "".join(xml_list)

  return xml_request, ext

################################################################################# 
# sendXmlString() - Send the xml string to the ZD and pickup the return string.
#
# args:
#	xml = XML string to send
#	nbi_url = ZD northbound interface URL
#
# return: response
################################################################################# 
def sendXmlString(xml, nbi_url):

  buf = cStringIO.StringIO()
  c=pycurl.Curl()
  c.setopt(c.FAILONERROR, True)
  c.setopt(c.HTTPHEADER, ['Accept: text/xml', 'Accept-Charset: UTF-8'])
  c.setopt(pycurl.SSL_VERIFYPEER, False) 
  c.setopt(c.POSTFIELDS,xml)
  c.setopt(c.WRITEFUNCTION, buf.write)
  try:
	c.setopt(c.URL, nbi_url)
	c.setopt(c.POSTFIELDS, xml)
	c.setopt(c.VERBOSE,True)
	c.perform()
  except:
	cgi.print_exception()
      
  response = buf.getvalue()
  buf.close  

  return response 
  

#################################################################### 
# checkXmlResponse() - check response status code
#
# args: 
#	xml_response = reply string
#
# returns: value
#################################################################### 
def checkXmlResponse(xml_response):

  doc = minidom.parseString(xml_response)
  node = doc.documentElement
  responses = doc.getElementsByTagName("response-code")
       
  for response in responses:
	nodes = response.childNodes
    
  for node in nodes:
	if node.nodeType == node.TEXT_NODE:
          value = node.data
      
  return value 



#################################################################### 
# getXmlAttribute() - extract a value from the ZD response by tag name
#
# args: 
#	xmlReplyFromZD = reply string
#	tag = tag name for value
#	attribute = attribute name
#
# returns: attribute value
#################################################################### 
def getXmlAttribute(xml_response,tag,attribute):

# Get the generated key
  doc = minidom.parseString(xml_response)
  for node  in doc.getElementsByTagName(tag):
	value = node.getAttribute(attribute)

  return value 

#################################################################### 
# getXmlTagData() - get the value of a tag from an XML string
#
# args: 
#	xml_response = XML string
#	tag = tag name for value
#
# returns: xmlData or none
#################################################################### 
def getXmlTagData(xml_response, tag):

  # Gets the value of the specified tag
  # In case the @param xml_response is not a well-formed XML, return None
  try:
      dom = minidom.parseString(xml_response)
      xmlTag = dom.getElementsByTagName(tag)[0].toxml()
      xmlData = xmlTag.replace('<%s>' % tag, '').replace('</%s>' % tag, '')

      return xmlData

  except:
      return None


     
####################################################################    
# statusCodeLookup() - check returned code from ZD
#	references the global list of response codes
#
# args: 
#	response_code = a success code to check
#
# returns: boolean indicating successful login
#################################################################### 
def statusCodeLookup(response_code, type):

  # What kind of operation is this?
  if type == "auth":
	# Find the first matching code number in authRespCodeList[]
	for x in authRespCodeList:
	  if x.code == response_code:
	  	# Found the code
 	  	return x.success 
  if type == "dpsk":
	# Find the first matching code number in dpskRespCodeList[]
	for x in dpskRespCodeList:
	  if x.code == response_code:
	  	# Found the code
 	  	return x.success 

  # No match 
  return False


####################################################################    
# class xmlRespCodes - response codes format
#
#	code = numerical code number
#	msg = status message
# 	success = True or False 
####################################################################    
class xmlRespCodes(object):

  def __init__(status, code=0, msg=None, success=0):
	status.code = code
	status.msg = msg
	status.success = success

####################################################################    
# class platform - OS platform
#
#	agent = partial user agent string
# 	name = name of platform for internal use
#	ext = executable extension name
####################################################################    
class platform(object):

  def __init__(platform, agent=None, name=None, ext=None):
	platform.agent = agent
	platform.name = name
	platform.ext = ext

#################################################################### 
# authRespCodeList - Global list of authentication response codes 
#	uses xmlRespCodes class
#################################################################### 
authRespCodeList = []
authRespCodeList.append(xmlRespCodes("100","Client is not authorized.",False))
authRespCodeList.append(xmlRespCodes("101","Login successful.",True))
authRespCodeList.append(xmlRespCodes("201","Login successful.",True))
authRespCodeList.append(xmlRespCodes("202","Authentication pending a response.",False))
authRespCodeList.append(xmlRespCodes("300","The name entered was not found. Please try again or contact your system admin.",False))
authRespCodeList.append(xmlRespCodes("301","Login failed. Check your user name and password.",False))
authRespCodeList.append(xmlRespCodes("302","Bad request. Please try again or contact your system admin.",False))
authRespCodeList.append(xmlRespCodes("303","Version not supported. Please contact your system admin.",False))
authRespCodeList.append(xmlRespCodes("400","ZoneDirector internal error. Please contact your system admin.",False))
authRespCodeList.append(xmlRespCodes("401","Authentication connection error or timeout. Please try again at a later time or contact your system admin.",False))

#################################################################### 
# dpskRespCodeList - Global list of response codes for DPSK generation
#	uses xmlRespCodes class
#################################################################### 
dpskRespCodeList = []
dpskRespCodeList.append(xmlRespCodes("100","Error: A new key cannot be created, because the maximum number of D-PSKs has been reached.",False))
dpskRespCodeList.append(xmlRespCodes("200","D-PSK successfully created.",True))
dpskRespCodeList.append(xmlRespCodes("255","D-PSK not found.",False))

#################################################################### 
# platformList - Global list of OS platforms for prov.exe
#	uses platform class
#################################################################### 
platformList = []
platformList.append(platform("iPod","iOS","mobileconfig"))
platformList.append(platform("iPhone","iOS","mobileconfig"))
platformList.append(platform("iPad","iOS","mobileconfig"))
platformList.append(platform("Android","android","apk"))
platformList.append(platform("Macintosh","macosx","app"))
platformList.append(platform("Windows NT 6.2","win62","exe")) # Windows 8 or Server 2012
platformList.append(platform("Windows NT 6.1","win61","exe")) # Windows 7 or Server 2008 R2
platformList.append(platform("Windows NT 6.0","win60","exe")) # Server 2008 or Vista
platformList.append(platform("Windows NT 5.2","win52","exe")) # Server 2003 or XP 64-bit
platformList.append(platform("Windows NT 5.1","win51","exe")) # XP 32-bit




