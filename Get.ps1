$url = "https://github.com/joachimschmidt557/DotStar/releases/download/v0.1.1-alpha/dotstar.exe"
$destination = Join-Path "$Env:LOCALAPPDATA" "DotStar" "dotstar.exe"
(New-Object System.Net.WebClient).DownloadFile($url, $destination)
