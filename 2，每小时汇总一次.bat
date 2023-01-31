
@echo off
mkdir log
:start
media_downloader >> .\log\%date:~0,4%%date:~5,2%%date:~8,2%.log
echo.
echo 正在等待，一小时之后再次汇总
timeout /t 3600
goto start