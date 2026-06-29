# VOD Studio - download local TTS model (ONNX) from HuggingFace.
# Pulls Supertone/supertonic-3 ONNX files into assets/onnx/ (no git-lfs needed).
# Models are not committed to the repo (GitHub 100MB limit); fetched on setup.
[CmdletBinding()]
param([switch]$Force)
$ErrorActionPreference = "Stop"
# The IWR progress bar throttles PowerShell 5.1 downloads massively (10-50x slower).
# Turning it off is the single biggest speed win for these large ONNX files.
$ProgressPreference = "SilentlyContinue"
# PowerShell 5.1 may default to old TLS; HuggingFace/Cloudflare require TLS 1.2.
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

$root = Split-Path -Parent $PSScriptRoot
$onnx = Join-Path $root "assets\onnx"
$base = "https://huggingface.co/Supertone/supertonic-3/resolve/main/onnx"
$files = @(
  "duration_predictor.onnx",
  "text_encoder.onnx",
  "vector_estimator.onnx",
  "vocoder.onnx",
  "tts.json",
  "unicode_indexer.json"
)

Write-Host "Downloading TTS model (HuggingFace Supertone/supertonic-3, ~380MB)" -ForegroundColor Cyan
Write-Host ("  target: " + $onnx)
New-Item -ItemType Directory -Force $onnx | Out-Null

foreach ($f in $files) {
  $dest = Join-Path $onnx $f
  if ((Test-Path $dest) -and (-not $Force)) {
    Write-Host ("  skip (exists): " + $f)
    continue
  }
  Write-Host ("  downloading: " + $f + " ...")
  # Download to a .part file, then rename on success so an interrupted run
  # never leaves a half-file that looks complete on the next run.
  $tmp = $dest + ".part"
  try {
    Invoke-WebRequest -Uri ($base + "/" + $f) -OutFile $tmp -UseBasicParsing
    Move-Item -Force $tmp $dest
  } catch {
    if (Test-Path $tmp) { Remove-Item -Force $tmp }
    Write-Host ("  [ERROR] " + $f + " download failed: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "  Check your internet connection and run setup.bat again." -ForegroundColor Yellow
    exit 1
  }
}
Write-Host "TTS model ready." -ForegroundColor Green
