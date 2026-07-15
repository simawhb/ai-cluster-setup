# Deploy startup scripts to all Worker machines
# Usage: powershell -ExecutionPolicy Bypass -File scripts\deploy-to-workers.ps1

$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force

$workers = @(
    @{ Name = "Worker 1"; IP = "192.168.31.110"; User = "ASUS" },
    @{ Name = "Worker 2"; IP = "192.168.31.50"; User = "ASUS" },
    @{ Name = "Worker 3"; IP = "192.168.31.139"; User = "14712" },
    @{ Name = "Worker 4"; IP = "192.168.31.216"; User = "whb" }
)

$sourceDir = "C:\Users\whb\ai-cluster-setup"

foreach ($w in $workers) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Deploy to $($w.Name) - $($w.IP)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    $cred = New-Object System.Management.Automation.PSCredential($w.User, $pass)

    try {
        # Test connection
        $session = New-PSSession -ComputerName $w.IP -Credential $cred -Authentication Basic -ErrorAction Stop
        Write-Host "Connected" -ForegroundColor Green

        # Remote path
        $remotePath = "C:\Users\$($w.User)\ai-cluster-setup"

        # Create directories
        Invoke-Command -Session $session -ScriptBlock {
            param($path)
            if (!(Test-Path $path)) {
                New-Item -ItemType Directory -Path $path -Force | Out-Null
                Write-Host "Created directory: $path"
            }
            if (!(Test-Path "$path\worker")) {
                New-Item -ItemType Directory -Path "$path\worker" -Force | Out-Null
            }
            if (!(Test-Path "$path\worker\bin")) {
                New-Item -ItemType Directory -Path "$path\worker\bin" -Force | Out-Null
            }
        } -ArgumentList $remotePath

        # Copy startup script
        Copy-Item -Path "$sourceDir\worker\start-worker-auto.bat" -Destination "$remotePath\worker\" -ToSession $session -Force
        Write-Host "Copied start-worker-auto.bat" -ForegroundColor Green

        # Copy cluster_worker.py
        Copy-Item -Path "$sourceDir\worker\cluster_worker.py" -Destination "$remotePath\worker\" -ToSession $session -Force
        Write-Host "Copied cluster_worker.py" -ForegroundColor Green

        # Copy config.py
        Copy-Item -Path "$sourceDir\config.py" -Destination "$remotePath\" -ToSession $session -Force
        Write-Host "Copied config.py" -ForegroundColor Green

        # Copy rpc-server.exe
        $rpcPath = "$sourceDir\bin\rpc-server.exe"
        if (Test-Path $rpcPath) {
            Copy-Item -Path $rpcPath -Destination "$remotePath\worker\bin\" -ToSession $session -Force
            Write-Host "Copied rpc-server.exe" -ForegroundColor Green
        }

        # Create desktop shortcut
        Invoke-Command -Session $session -ScriptBlock {
            param($remotePath, $userName)
            $desktopPath = "C:\Users\$userName\Desktop"
            $shortcutPath = "$desktopPath\StartAIWorker.lnk"

            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = "$remotePath\worker\start-worker-auto.bat"
            $shortcut.WorkingDirectory = "$remotePath\worker"
            $shortcut.Description = "Start AI Cluster Worker"
            $shortcut.Save()

            Write-Host "Created desktop shortcut" -ForegroundColor Green
        } -ArgumentList $remotePath, $w.User

        Remove-PSSession $session
        Write-Host "Deploy complete" -ForegroundColor Green

    } catch {
        Write-Host "Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All deployment complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "On each Worker, double-click 'StartAIWorker' shortcut on desktop" -ForegroundColor Yellow
