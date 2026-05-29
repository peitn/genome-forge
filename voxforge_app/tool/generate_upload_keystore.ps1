param(
    [string]$Out = "$HOME\upload-keystore.jks"
)

Write-Host "Creating Android upload keystore at: $Out"
keytool -genkey -v `
  -keystore "$Out" `
  -keyalg RSA `
  -keysize 2048 `
  -validity 10000 `
  -alias upload

Write-Host "Done. Copy android/key.properties.example to android/key.properties and set storeFile=$Out"
