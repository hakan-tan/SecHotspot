@ECHO OFF
REM 
REM  The northbound-batch.cmd is a Windows Command Script used to test  
REM  Northbound Interface via the curl.exe program.
REM
REM  Usage:
REM    Just double click on it to run the interative mode.
REM    OR, provide all the parameters. See below for detail.
REM
REM  northbound-batch[.cmd] [command] [host] [loop] [delay]
REM    command: list of commands supported and NOT supported in this version:
REM      > user-authenticate: Supported. [3.3.1.1 Authentication request]
REM      > check-user-status: Supported. [3.3.1.2 User status query]
REM      > del-user: Supported. [3.3.1.3 Teminating user session]
REM      > unrestricted: Supported. [3.3.2 Unrestricted mode for Hotspot user]
REM      > get-prov-file: Supported [3.3.3 Download Zero-IT activation (prov.exe) to web portal]
REM      > "user_extern_prov.jsp": NOT supported. [3.3.4 Download Zero-IT activation application (prov.exe) by user without ZD authentication]
REM      > get-client: Supported. [3.3.5 Query client information for Web portal]
REM      > generate-dpsk: Supported. [3.3.6.1 Generate a DPSK entry]
REM      > get-dpsk: Supported. [3.3.6.2 Retrieve DPSK entry]
REM    host: ZD IP Address
REM    loop: number of times to execute 
REM    delay: number of seconds to pause
REM
REM  Input:
REM    An xml file named <command>.xml, where command is the user input parameter.
REM
REM  Output:
REM    One to many files in the format: <command>-out<[1-n]>.<[xml|exe]>.
REM    The output extension is exe in the case of get-prov-file.
REM  
REM  Example1: northbound-batch get-prov-file 172.31.128.25 5 2
REM    > Generate Zero-IT for WebPortal. 
REM      Generate 5 provision files and pause 2 seconds between each. 
REM  
REM  Example2: northbound-batch (Enter)
REM    > Run one time only, without loop.
REM      Enter a command: get-prov-file
REM      Enter Host IP Address: 172.31.128.25
REM
REM  @created: 2012/01/05
REM  @modified: 2013/02/27
REM  @author: Phan Nguyen
REM  

@ECHO OFF
REM ---Clear saved params---
:CLEANUP
FOR %%p in (MYCMD, IPADDR, COUNT) DO (
    SET %%p=
)

REM ---Check if a command is entered---
:NEEDCMD
IF NOT (%1)==() (
    SET MYCMD=%1
) ELSE (
    SET /P MYCMD=Enter a command: 
)
IF (%MYCMD%)==() (
    GOTO NEEDCMD
)

REM ---Check if the Host IP Address is entered---
:NEEDHOST
IF NOT (%2)==() (
    SET IPADDR=%2
) ELSE (
    SET /P IPADDR=Enter Host IP Address: 
)
IF (%IPADDR%)==() (
    GOTO NEEDHOST
)

REM ---Number of times to execute the command---
IF NOT (%3)==() (
    SET COUNT=%3
) ELSE (
    SET COUNT=1
)

REM ---Delay time between executions---
IF NOT (%4)==() (
    SET SLEEP=%4
) ELSE (
    SET SLEEP=0
)

REM ---This is the Main---
:MAIN
SET POSTURL=https://%IPADDR%/admin/_portalintf.jsp
SET BASEOUT=%MYCMD%-out

SET EXT=xml
IF (%MYCMD%)==(get-prov-file) (
    SET EXT=exe
)

FOR /L %%i in (1, 1, %COUNT%) DO (
    ECHO.
	ECHO.
	TYPE %MYCMD%.xml | CURL.EXE -k -d @- -o %BASEOUT%%%i.%EXT% %POSTURL%
	ECHO.Please see the output file: %BASEOUT%%%i.%EXT%
	ECHO.
	IF NOT %%i==%COUNT% (
	    ECHO.Waiting %SLEEP% seconds before the next exec...
	    CHOICE /D Y /T %SLEEP% >NUL
	) ELSE (
	    PAUSE
	)
)
