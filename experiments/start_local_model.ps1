param([string]$CacheDir = (Join-Path $env:TEMP 'overclaim_model_cache'), [int]$Port = 8127)
$ErrorActionPreference = 'Stop'
$taskCache = [System.IO.Path]::GetFullPath($CacheDir)
$taskBinary = Join-Path $taskCache 'llama\llama-server.exe'
$taskModel = Join-Path $taskCache 'qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf'
if (!(Test-Path -LiteralPath $taskBinary) -or !(Test-Path -LiteralPath $taskModel)) { throw 'Run experiments/setup_runtime.py first.' }
$taskArgs = @('-m', ('"' + $taskModel + '"'), '--host', '127.0.0.1', '--port', "$Port", '--ctx-size', '4096', '--n-gpu-layers', '99', '--parallel', '1', '--flash-attn', 'on', '--no-webui')
$taskProcess = Start-Process -FilePath $taskBinary -ArgumentList $taskArgs -WorkingDirectory $taskCache -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskCache 'server.stdout.log') -RedirectStandardError (Join-Path $taskCache 'server.stderr.log') -PassThru
$taskProcess.Id | Set-Content -LiteralPath (Join-Path $taskCache 'server.pid')
Write-Output "Started local model PID $($taskProcess.Id) at http://127.0.0.1:$Port"
Write-Output 'Wait for /health to return status ok before running experiments.'
