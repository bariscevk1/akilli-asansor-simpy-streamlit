$ErrorActionPreference = "Stop"

if (Get-Command py -ErrorAction SilentlyContinue) {
  py -m pip install -r requirements.txt
  exit 0
}

if (Get-Command python -ErrorAction SilentlyContinue) {
  python -m pip install -r requirements.txt
  exit 0
}

Write-Host "Python bulunamadi. Python 3.10+ kurup tekrar deneyin."
exit 1

