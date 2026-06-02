$ErrorActionPreference = "SilentlyContinue"

while ($true) {
    # Fetch data FIRST (this takes ~300ms, so we do it before clearing the screen!)
    $endpoints = docker exec nexpulse-redis redis-cli ZREVRANGE leaderboard:endpoints 0 5 WITHSCORES
    $countries = docker exec nexpulse-redis redis-cli ZREVRANGE leaderboard:countries 0 5 WITHSCORES

    # Now clear screen and draw instantly
    Clear-Host
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "        >>> NEXPULSE LIVE TERMINAL ANALYTICS <<<  " -ForegroundColor White -BackgroundColor DarkBlue
    Write-Host "==================================================`n" -ForegroundColor Cyan
    
    if ($null -ne $endpoints -and $endpoints.Count -ge 2) {
        $maxScore = [double]$endpoints[1]
        
        Write-Host ">>> LIVE TOP ENDPOINTS (Requests/sec)" -ForegroundColor Yellow
        Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
        
        for ($i = 0; $i -lt $endpoints.Count; $i += 2) {
            $endpoint = $endpoints[$i].Trim()
            $scoreStr = $endpoints[$i+1].Trim()
            $score = [double]$scoreStr
            
            # Scale bar to max 30 characters
            $barLength = 0
            if ($maxScore -gt 0) {
                $barLength = [math]::Round(($score / $maxScore) * 30)
            }
            
            $bar = "".PadRight($barLength, [char]0x2588)
            $paddingLength = 15 - $endpoint.Length
            if ($paddingLength -lt 0) { $paddingLength = 0 }
            $padding = " " * $paddingLength
            
            Write-Host "$endpoint $padding | " -NoNewline -ForegroundColor White
            Write-Host $bar -NoNewline -ForegroundColor Green
            Write-Host " $scoreStr" -ForegroundColor Gray
        }
    } else {
        Write-Host "Waiting for traffic data..." -ForegroundColor DarkGray
    }

    Write-Host "`n"
    
    if ($null -ne $countries -and $countries.Count -ge 2) {
        $maxCScore = [double]$countries[1]
        
        Write-Host ">>> LIVE TOP COUNTRIES" -ForegroundColor Magenta
        Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
        
        for ($i = 0; $i -lt $countries.Count; $i += 2) {
            $country = $countries[$i].Trim()
            $scoreStr = $countries[$i+1].Trim()
            $score = [double]$scoreStr
            
            $barLength = 0
            if ($maxCScore -gt 0) {
                $barLength = [math]::Round(($score / $maxCScore) * 30)
            }
            
            $bar = "".PadRight($barLength, [char]0x2588)
            $paddingLength = 15 - $country.Length
            if ($paddingLength -lt 0) { $paddingLength = 0 }
            $padding = " " * $paddingLength
            
            Write-Host "$country $padding | " -NoNewline -ForegroundColor White
            Write-Host $bar -NoNewline -ForegroundColor Magenta
            Write-Host " $scoreStr" -ForegroundColor Gray
        }
    }

    Write-Host "`nPress Ctrl+C to exit." -ForegroundColor DarkGray
    Start-Sleep -Seconds 1
}
