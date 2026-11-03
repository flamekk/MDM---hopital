param([switch]$Installer)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Création de l’environnement échouée.' }
    $Installer = $true
}
if ($Installer) {
    & $projectPython -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances échouée.' }
}
if (-not (Test-Path -LiteralPath 'workspace_hospital\S1_5pct\sources')) {
    & $projectPython -m mdm hospital-demo --workspace workspace_hospital
    if ($LASTEXITCODE -ne 0) { throw 'Initialisation échouée.' }
}
& $projectPython -m streamlit run app.py
