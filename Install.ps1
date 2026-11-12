$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$SourceDir = $PSScriptRoot
$Target = 'C:\WildbberriesClient'
$Payload = Join-Path $SourceDir 'ClientPayload.zip'
$BuiltApp = Join-Path $SourceDir 'dist\WildbberriesClient'
$Exe = Join-Path $BuiltApp 'WildbberriesClient.exe'
if (-not (Test-Path -LiteralPath $Payload)) { throw 'Не найден ClientPayload.zip.' }
if (-not (Test-Path -LiteralPath $Exe)) { throw 'Сначала запусти Build.bat и дождись сборки dist\WildbberriesClient\WildbberriesClient.exe.' }

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"'))
    exit
}

New-Item -ItemType Directory -Path $Target -Force | Out-Null
$runDir = Join-Path $Target 'run'
$backup = Join-Path $env:TEMP ('WildbberriesClient-run-' + [guid]::NewGuid().ToString('N'))
$hadRun = Test-Path -LiteralPath $runDir
if ($hadRun) { Move-Item -LiteralPath $runDir -Destination $backup -Force }
try {
    Expand-Archive -LiteralPath $Payload -DestinationPath $Target -Force
    if ($hadRun -and (Test-Path -LiteralPath $backup)) {
        if (Test-Path -LiteralPath $runDir) { Remove-Item -LiteralPath $runDir -Recurse -Force }
        Move-Item -LiteralPath $backup -Destination $runDir -Force
    }
} catch {
    if ($hadRun -and (Test-Path -LiteralPath $backup)) {
        if (Test-Path -LiteralPath $runDir) { Remove-Item -LiteralPath $runDir -Recurse -Force }
        Move-Item -LiteralPath $backup -Destination $runDir -Force
    }
    throw
}

Get-ChildItem -LiteralPath $BuiltApp -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Target -Recurse -Force
}
$assets = Join-Path $SourceDir 'assets'
if (Test-Path -LiteralPath $assets) { Copy-Item -LiteralPath $assets -Destination $Target -Recurse -Force }
$settingsSource = Join-Path $SourceDir 'launcher-settings.json'
$settingsTarget = Join-Path $Target 'launcher-settings.json'
if ((Test-Path $settingsSource) -and -not (Test-Path $settingsTarget)) { Copy-Item $settingsSource $settingsTarget }
if (-not (Test-Path (Join-Path $Target 'run-client.bat'))) { throw 'В ClientPayload.zip не найден run-client.bat.' }
if (-not (Test-Path (Join-Path $Target '.launcher-version'))) { Set-Content -Path (Join-Path $Target '.launcher-version') -Value '1.1.0' -Encoding ASCII }

$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'WildbberriesClient.lnk'
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = Join-Path $Target 'WildbberriesClient.exe'
$sc.WorkingDirectory = $Target
$icon = Join-Path $Target 'assets\wildbberries.ico'
if (Test-Path $icon) { $sc.IconLocation = $icon }
$sc.Save()
[System.Windows.Forms.MessageBox]::Show("WildbberriesClient установлен в $Target`nПапка run сохранена.", 'Установка завершена', 'OK', 'Information') | Out-Null
