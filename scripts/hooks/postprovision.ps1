$ErrorActionPreference = "Stop"

if (Get-Command python -ErrorAction SilentlyContinue) {
  python .\scripts\entra\sync_apps.py --mode postprovision
  exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
  py .\scripts\entra\sync_apps.py --mode postprovision
  exit $LASTEXITCODE
}

throw "Python is required to configure Microsoft Entra app registrations."
