# Sign Windows executable using self-signed certificate (for testing)
# Usage: .\sign_app_selfsigned.ps1 [exe_path]
#
# This should be run BEFORE creating the installer with Inno Setup.
#
# Note: This is for testing only. Users will see security warnings.
# For production, use Azure Trusted Signing or a commercial certificate.

param(
    [string]$ExePath
)

$ErrorActionPreference = "Stop"

$AppName = "PitchGrid Mapper"
$AppVersion = "0.1.0"

Write-Host "Creating self-signed certificate for testing..." -ForegroundColor Cyan

# Find executable to sign
if (-not $ExePath) {
    $ExePath = "dist\$AppName\$AppName.exe"
}

if (-not (Test-Path $ExePath)) {
    Write-Host "Error: Executable not found at $ExePath" -ForegroundColor Red
    Write-Host "Build the app first, or specify path: .\sign_app_selfsigned.ps1 path\to\app.exe" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Executable: $ExePath"

# Check if certificate already exists
$certName = "CN=PitchGrid Development Certificate"
$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $certName } | Select-Object -First 1

if (-not $cert) {
    Write-Host ""
    Write-Host "Creating new self-signed certificate..." -ForegroundColor Yellow

    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $certName `
        -CertStoreLocation Cert:\CurrentUser\My `
        -NotAfter (Get-Date).AddYears(3) `
        -HashAlgorithm SHA256

    Write-Host "  Certificate created: $($cert.Thumbprint)"
}
else {
    Write-Host ""
    Write-Host "Using existing certificate: $($cert.Thumbprint)" -ForegroundColor Yellow
}

# Sign the executable
Write-Host ""
Write-Host "Signing executable..." -ForegroundColor Yellow

try {
    Set-AuthenticodeSignature -FilePath $ExePath -Certificate $cert -TimestampServer "http://timestamp.digicert.com"
    Write-Host "  Signing completed!" -ForegroundColor Green
}
catch {
    Write-Host "  Error signing executable: $_" -ForegroundColor Red
    exit 1
}

# Verify signature
Write-Host ""
Write-Host "Verifying signature..." -ForegroundColor Yellow

$sig = Get-AuthenticodeSignature $ExePath
Write-Host "  Signature Status: $($sig.Status)"
Write-Host "  Signer: $($sig.SignerCertificate.Subject)"

if ($sig.Status -eq "UnknownError") {
    Write-Host ""
    Write-Host "Note: 'UnknownError' is normal for self-signed certificates" -ForegroundColor Cyan
    Write-Host "The certificate is not in the Trusted Root store" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "  - This is a self-signed certificate for TESTING ONLY" -ForegroundColor Yellow
Write-Host "  - Status 'UnknownError' is expected (cert not in Trusted Root)" -ForegroundColor Yellow
Write-Host "  - Users will see security warnings when installing" -ForegroundColor Yellow
Write-Host "  - For production distribution, use Azure Trusted Signing" -ForegroundColor Yellow
Write-Host ""
Write-Host "Signed executable:" -ForegroundColor Cyan
Write-Host "  $ExePath"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Create installer: .\create_installer.ps1"
Write-Host "  2. Sign installer: .\sign_installer_selfsigned.ps1"
