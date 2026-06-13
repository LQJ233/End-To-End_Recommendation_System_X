Param(
  [int]$Workers = 1,
  [int]$RecallIoWorkers = 32,
  [int]$RankingCpuWorkers = 0,
  [double]$TimeoutSec = 2.5
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = $root
$env:RECSYS_RECALL_IO_WORKERS = $RecallIoWorkers
if ($RankingCpuWorkers -gt 0) {
  $env:RECSYS_RANKING_CPU_WORKERS = $RankingCpuWorkers
}
$env:RECSYS_REQUEST_TIMEOUT_SEC = $TimeoutSec
# 注意: torch 模型在 fork 多进程下不能共享内存; 这里 --workers 1 + 进程内线程池.
# 真要横向扩, 应该跑多个独立进程, 分别监听不同端口, 由后端负载均衡.
python -m uvicorn algorithm.inference.app:app --host 0.0.0.0 --port 9000 --log-level info --workers $Workers
