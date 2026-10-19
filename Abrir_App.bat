@echo off
rem Abre o app Gestao de Demandas no navegador (duplo clique neste arquivo).
rem Para fechar o app: feche esta janela preta.
chcp 65001 > nul
cd /d "%~dp0"

set "PY=C:\Users\18-103236\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"

echo Abrindo Gestao de Demandas... o navegador abre sozinho em alguns segundos.
echo Se nao abrir, acesse: http://localhost:8501
echo Para FECHAR o app, feche esta janela.
echo.

"%PY%" -m streamlit run app.py --server.port 8501
if errorlevel 1 (
  echo.
  echo Deu erro ao abrir. Tentando instalar as dependencias e abrir de novo...
  "%PY%" -m pip install -r requirements.txt
  "%PY%" -m streamlit run app.py --server.port 8501
)
pause
