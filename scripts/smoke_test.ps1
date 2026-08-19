# KappaLake smoke test - validates the whole stack end-to-end.
# Usage: powershell -File scripts/smoke_test.ps1
$ErrorActionPreference = "SilentlyContinue"

Write-Host "== KappaLake smoke test =="

function Check($name, $url, $method = "GET", $body = $null) {
    try {
        if ($body) {
            $r = Invoke-WebRequest -Uri $url -Method $method -ContentType "application/json" -Body $body -UseBasicParsing -TimeoutSec 180
        } else {
            $r = Invoke-WebRequest -Uri $url -Method $method -UseBasicParsing -TimeoutSec 60
        }
        Write-Host "[OK]   $name ($($r.StatusCode))"
    } catch {
        Write-Host "[FAIL] $name -> $($_.Exception.Message)"
    }
}

Check "API health"             "http://localhost:8000/health"
Check "API catalog"            "http://localhost:8000/catalog/tables"
Check "API query (silver)"     "http://localhost:8000/query/execute" "POST" '{"query":"SELECT count(*) AS n FROM iceberg.silver.users"}'
Check "Hayai /v1/models"        "http://localhost:8085/v1/models"
Check "Trino /v1/info"         "http://localhost:8080/v1/info"
Check "Keycloak realm"         "http://localhost:8180/realms/kappalake/.well-known/openid-configuration"
Check "KappaLake UI"           "http://localhost:3001"
Check "Dagster UI"             "http://localhost:3000"
Check "MinIO console"          "http://localhost:9001"

Write-Host "== Done =="
