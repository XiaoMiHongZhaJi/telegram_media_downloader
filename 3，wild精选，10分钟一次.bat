
@echo off

:start
wild_like_message
echo.
echo 正在等待，10分钟之后再次汇总
timeout /t 600
goto start