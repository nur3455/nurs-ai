@echo off
title MyAI Chatbot

cd /d "%~dp0"

echo =================================
echo       Starting MyAI Chatbot
echo =================================
echo.

python -m streamlit run app.py

echo.
echo MyAI has stopped.
pause