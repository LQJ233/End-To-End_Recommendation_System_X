Param(
  [string]$NginxExe = "C:\openresty\nginx.exe"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
& $NginxExe -p (Join-Path $root "data-pipeline/nginx") -c "nginx.conf"
