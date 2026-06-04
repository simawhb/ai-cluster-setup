# Server酱通知脚本
param(
    [string]$Title = "AI Cluster Notification",
    [string]$Desp = "No content",
    [string]$SendKey = "SCT358949TQ6dXH87kNRLLVcGc9BkoLCYt"
)

$url = "https://sctapi.ftqq.com/$SendKey.send"
$body = "title=$Title&desp=$Desp"

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/x-www-form-urlencoded; charset=utf-8"
    Write-Host "Notification sent successfully: $($response | ConvertTo-Json -Compress)"
} catch {
    Write-Host "Notification failed: $($_.Exception.Message)"
}
