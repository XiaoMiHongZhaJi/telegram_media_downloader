
@echo off
mkdir log
:start
media_downloader >> .\log\%date:~0,4%%date:~5,2%%date:~8,2%.log
echo.
echo ���ڵȴ���һСʱ֮���ٴλ���
timeout /t 3600
goto start