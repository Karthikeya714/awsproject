@echo off
echo ========================================
echo   IMAGE CAPTION GENERATOR - AUTH APP
echo ========================================
echo.
echo Starting the application with LOGIN/SIGNUP pages...
echo.
echo The app will open in your browser automatically.
echo Look for: SIGNIN page or SIGNUP page
echo.
echo Press Ctrl+C to stop the app
echo ========================================
echo.

cd /d d:\genaiproject
call venv\Scripts\activate.bat
streamlit run app\streamlit_app_auth.py
