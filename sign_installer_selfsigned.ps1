# Sign Windows installer using self-signed certificate (for testing)
# Usage: .\sign_installer_selfsigned.ps1 [installer_path]
#
# Note: This is for testing only. Users will see security warnings.
# For production, use Azure Trusted Signing or a commercial certificate.

param(
    [string]$InstallerPath
)

$ErrorActionPreference = "Stop"

$AppName = "PGIsomap"
$AppVersion = "0.1.0"

Write-Host "Creating self-signed certificate for testing..." -ForegroundColor Cyan

# Find installer to sign
if (-not $InstallerPath) {
    $OutputDir = "Installers\Windows\Output"
    $InstallerFile = Get-ChildItem "$OutputDir\*.exe" -ErrorAction SilentlyContinue |
                     Sort-Object LastWriteTime -Descending |
                     Select-Object -First 1
    if ($InstallerFile) {
        $InstallerPath = $InstallerFile.FullName
    }
}

if (-not $InstallerPath -or -not (Test-Path $InstallerPath)) {
    Write-Host "Error: No installer found to sign" -ForegroundColor Red
    Write-Host "Run .\create_installer.ps1 first, or specify path: .\sign_installer_selfsigned.ps1 path\to\installer.exe" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Installer: $InstallerPath"

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

# Sign the installer
Write-Host ""
Write-Host "Signing installer..." -ForegroundColor Yellow

try {
    Set-AuthenticodeSignature -FilePath $InstallerPath -Certificate $cert -TimestampServer "http://timestamp.digicert.com"
    Write-Host "  Signing completed!" -ForegroundColor Green
}
catch {
    Write-Host "  Error signing installer: $_" -ForegroundColor Red
    exit 1
}

# Verify signature
Write-Host ""
Write-Host "Verifying signature..." -ForegroundColor Yellow

$sig = Get-AuthenticodeSignature $InstallerPath
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
Write-Host "Signed installer (self-signed for testing):" -ForegroundColor Green
Write-Host "  $InstallerPath"
Write-Host ""
Write-Host "The installer is signed but users will see warnings. Use Azure Trusted Signing for production." -ForegroundColor Cyan
