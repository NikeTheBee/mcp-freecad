@echo off
REM ============================================================
REM  Lance le serveur FreeCAD headless pour le MCP (localhost:23456).
REM  Double-clique ce fichier et LAISSE LA FENETRE OUVERTE.
REM  Ensuite, ouvre une conversation Claude Code dans ce dossier
REM  et demande en langage naturel (ex: "cree une boite 30x20x10mm").
REM ============================================================

set "FCBIN=%FREECAD_MCP_FREECAD_BIN%"
if "%FCBIN%"=="" set "FCBIN=A:\FreeCAD\bin\freecadcmd.exe"

set "SERVER=%APPDATA%\FreeCAD\Mod\AICopilot\headless_server.py"

if not exist "%FCBIN%" (
  echo [ERREUR] FreeCAD introuvable: %FCBIN%
  echo Definis FREECAD_MCP_FREECAD_BIN ou corrige le chemin.
  pause
  exit /b 1
)
if not exist "%SERVER%" (
  echo [ERREUR] AICopilot introuvable: %SERVER%
  echo Lance d'abord:  python install\bootstrap.py
  pause
  exit /b 1
)

echo Demarrage du serveur FreeCAD MCP sur localhost:23456 ...
echo (Laisse cette fenetre ouverte pendant que tu utilises Claude.)
"%FCBIN%" "%SERVER%"
pause
