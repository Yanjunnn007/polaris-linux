Write-Output '=== USB devices (OK) ==='
Get-PnpDevice | Where-Object {$_.Status -eq 'OK' -and $_.InstanceId -match 'D001|POSTMARKETOS|VID_18D1|NCM'} | Select-Object Status,Class,FriendlyName | Format-Table -AutoSize | Out-String -Width 150
Write-Output '=== NCM network adapters ==='
Get-NetAdapter | Where-Object {$_.InterfaceDescription -match 'NCM|RNDIS|NDIS|Linux|USB'} | Select-Object Name,Status,InterfaceDescription | Format-Table -AutoSize | Out-String -Width 150
Write-Output '=== PMOS volume ==='
Get-Volume | Where-Object {$_.FileSystemLabel -match 'PMOS'} | Select-Object DriveLetter,FileSystemLabel | Format-Table -AutoSize | Out-String
