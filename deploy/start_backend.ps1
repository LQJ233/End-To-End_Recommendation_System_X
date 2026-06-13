Param(
  [string]$Profile = "local"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "backend")
$env:SPRING_PROFILES_ACTIVE = $Profile
mvn -q spring-boot:run
