chcp 65001
if ([string]::IsNullOrWhiteSpace($args[0])){
    echo "请输入BOT_HOME"
}
Set-Content env:BOT_HOME $args[0]
$env_path = "$env:BOT_HOME/.env"
echo $env_path

if(!(Test-Path $env_path)){exit}
Get-Content $env_path -Encoding utf8 | foreach {
    $name, $value = $_.split('=')
    if (!([string]::IsNullOrWhiteSpace($name)) -and !($name.Contains('#'))) {
        [Environment]::SetEnvironmentVariable($name.trim(), $value.trim())
    }
}
python ".\main.py"
pause
