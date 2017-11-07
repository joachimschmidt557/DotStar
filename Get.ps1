$url = "https://github.com/joachimschmidt557/DotStar/releases/download/v0.1.1-alpha/dotstar.exe"
$file = Join-Path "$(Split-Path -Parent $MyInvocation.MyCommand.Definition)" "dotstar.exe"
$destination = Join-Path "$Env:LOCALAPPDATA" "DotStar"
(New-Object System.Net.WebClient).DownloadFile($url, $file)
Move-Item $file $destination -Force
