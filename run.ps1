chcp 65001 | out-null
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = $PSDefaultParameterValues['*:Encoding'] = [System.Text.Encoding]::Utf8
if ([string]::IsNullOrWhiteSpace($args[0])){
    echo "请输入BOT_HOME"
    exit
}
Set-Content env:BOT_HOME $args[0]
$env_path = "$env:BOT_HOME/.env"

if (Test-Path '.venv\') {
    $flag = $false
    $runFilePath = ".venv\Scripts\python.exe"
} else {
    $flag = $true
    $runFilePath = "python.exe"
}
ps python | foreach {
    $l, $l, $name = $_.CommandLine.split(' ')
    if ( "$name" -like "$env:BOT_HOME" -and ($flag -or $_.CommandLine.Contains(".venv")) ) {
        echo "机器人运行中 pid: $($_.id)"
        exit
    }
}

if(!(Test-Path $env_path)){
    echo "$env_path 不存在, exit"
    exit
}else{
    echo "读取 $env_path"
}
Get-Content $env_path -Encoding utf8 | foreach {
    $name, $value = $_.split('=')
    if (!([string]::IsNullOrWhiteSpace($name)) -and !($name.Contains('#'))) {
        [Environment]::SetEnvironmentVariable($name.trim(), $value.trim())
    }
}

$p = Start-Process -FilePath $runFilePath -ArgumentList ".\main.py","$env:BOT_HOME" -WindowStyle Hidden -PassThru -RedirectStandardOutput $env:BOT_HOME/bot.log 
echo "运行至pid: $($p.id)"