Param(
  [string]$DbUser = "root",
  [string]$DbPass = "change_me",
  [string]$DbHost = "localhost",
  [int]$DbPort = 3306,
  [string]$DbName = "end_to_end_recommendation_system_x"
)
$ErrorActionPreference = "Stop"

# Flyway 鎺ョ鎵€鏈?DDL/DML; 杩欓噷鍙‘淇?database 瀛樺湪.
$createDb = "CREATE DATABASE IF NOT EXISTS $DbName DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h $DbHost -P $DbPort -u $DbUser -p"$DbPass" -e $createDb

Write-Host "Database '$DbName' ensured."
Write-Host "Now start the backend; Flyway will apply migrations on startup:"
Write-Host "    ./deploy/start_backend.ps1"
Write-Host ""
Write-Host "(鑴氭湰 scripts/sql/*.sql 浠呬綔涓哄弬鑰冧繚鐣? 涓嶅啀鐢ㄤ簬鍒濆鍖?"
