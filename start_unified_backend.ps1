$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $repo "backend"

$pythonCandidates = @(
    "c:/Users/aarya/OneDrive/Desktop/inti1/.venv/Scripts/python.exe",
    (Join-Path $repo ".venv/Scripts/python.exe")
)

$python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $python) {
    throw "No Python executable found in known virtual environments."
}

Write-Host "Using Python: $python"

Start-Process -FilePath $python -ArgumentList "`"$repo/mock_stt_9000.py`"" -WorkingDirectory $repo | Out-Null
Start-Sleep -Milliseconds 300
Start-Process -FilePath $python -ArgumentList "`"$repo/mock_tts_9011.py`"" -WorkingDirectory $repo | Out-Null
Start-Sleep -Milliseconds 300
Start-Process -FilePath $python -ArgumentList "`"$repo/mock_llm_9002.py`"" -WorkingDirectory $repo | Out-Null
Start-Sleep -Milliseconds 500
Start-Process -FilePath $python -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8011" -WorkingDirectory $backend | Out-Null

Write-Host "Unified stack started:"
Write-Host "  Backend: http://127.0.0.1:8011"
Write-Host "  STT:     http://127.0.0.1:9000"
Write-Host "  TTS:     http://127.0.0.1:9011"
Write-Host "  LLM:     http://127.0.0.1:9002"
Write-Host ""
Write-Host "Verify:"
Write-Host "  Invoke-RestMethod http://127.0.0.1:8011/"
Write-Host "  Invoke-RestMethod http://127.0.0.1:8011/calls/health"
