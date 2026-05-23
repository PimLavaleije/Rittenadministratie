@echo off
echo Rittenadministratie starten...

if not exist venv (
    echo Virtuele omgeving aanmaken...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Packages installeren...
pip install -q -r requirements.txt

if not exist .env (
    copy .env.example .env
    echo .env aangemaakt. Pas de waarden aan indien nodig.
)

echo.
echo App starten op http://localhost:5000
echo Druk op Ctrl+C om te stoppen.
echo.

python app.py
pause
