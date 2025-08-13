@echo off
REM Script de instalación para Windows - McDVoice Bot

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no está instalado o no está en el PATH.
    echo Descárgalo desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Crear entorno virtual
echo 🛠️ Creando entorno virtual...
python -m venv venv

:: Activar entorno virtual
echo 🔌 Activando entorno virtual...
call venv\Scripts\activate.bat

:: Instalar Selenium
echo 📦 Instalando Selenium...
pip install selenium

:: Descargar Geckodriver
echo 🦊 Descargando Geckodriver para Windows...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-win64.zip' -OutFile 'geckodriver.zip'"

:: Extraer y configurar Geckodriver
echo ⚙️ Configurando Geckodriver...
powershell -Command "Expand-Archive -Path 'geckodriver.zip' -DestinationPath 'geckodriver'"
move /Y geckodriver\geckodriver.exe venv\Scripts\ >nul
rmdir /S /Q geckodriver
del geckodriver.zip

:: Verificar instalación
echo ✅ Verificando instalación...
python -c "import selenium; print('✓ Selenium instalado correctamente')" || (
    echo ❌ Error al verificar Selenium
    pause
    exit /b 1
)

venv\Scripts\geckodriver.exe --version >nul 2>&1 || (
    echo ❌ Error al verificar Geckodriver
    pause
    exit /b 1
)

echo.
echo 🎉 ¡Instalación completada!
echo Ejecuta el bot con:
echo    venv\Scripts\activate.bat
echo    python mcdvoice_bot.py
pause
