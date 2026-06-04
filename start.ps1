$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting NexPulse Services in separate windows..." -ForegroundColor Cyan

# Define the services to start
$services = @(
    @{ Name = "Gateway"; Path = "services\gateway"; Port = 8080 },
    @{ Name = "Query"; Path = "services\query"; Port = 8081 },
    @{ Name = "Aggregator"; Path = "services\aggregator"; Port = 8082 },
    @{ Name = "Anomaly"; Path = "services\anomaly"; Port = 8083 },
    @{ Name = "Simulator"; Path = "tools\simulator"; Args = "--rate 1000 --workers 20" }
)

foreach ($service in $services) {
    Write-Host "Starting $($service.Name)..." -ForegroundColor Yellow
    
    $argsString = "go run ."
    if ($service.Args) {
        $argsString += " $($service.Args)"
    }

    # Open a new PowerShell window, change directory, and run the service
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $($service.Path); title '$($service.Name)'; $argsString"
    
    Start-Sleep -Seconds 1 # small delay to prevent rapid-fire window popups overlapping
}

Write-Host "✅ All services launched!" -ForegroundColor Green
Write-Host "You can also run the terminal dashboard with: .\dashboard.ps1" -ForegroundColor Cyan
