Write-Host Quick Dotstar Installer

Write-Host Downloading DotStar...
$url = "https://github.com/joachimschmidt557/DotStar/releases/download/v0.1.1-alpha/dotstar.exe"
$destination = Join-Path (Join-Path "$Env:LOCALAPPDATA" "DotStar") "dotstar.exe"
(New-Object System.Net.WebClient).DownloadFile($url, $destination)

Write-Host Refreshing packages...
Start-Process $destination -ArgumentList "refresh" -NoNewWindow -Wait

Write-Host Installing DotStar...
Start-Process $destination -ArgumentList "-i dotstar" -NoNewWindow -Wait
