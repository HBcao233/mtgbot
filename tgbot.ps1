
param(
  [string]$1={throw "用法: $0 {start|restart|stop|status|log}"},
  [string]$bot_name
)
chcp 65001 | out-null
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = [System.Text.Encoding]::Utf8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$0 = $MyInvocation.InvocationName

class Bot {
  [string] $name 
  [int] $pid = 0
  [bool] $status = 0
  [System.Datetime] $start
  [string] $ago

  Bot ([string] $name) { 
    $this.name = $name
  }
}

$root=($pwd).path
$bots = @{}
$venv = Test-Path ".venv\"
foreach ($i in Get-ChildItem $root) {
  $dirname = $i.name
  if ((Test-Path $i -PathType Container) -and (Test-Path "$dirname\.env" -PathType Leaf)){
    $bots[$dirname] = [Bot]::new($dirname)
  }
}
if ($bots.count -eq 0) {
  echo "当前无机器人, 请新建一个文件夹, 并放入一个 .env 文件, 脚本将该文件夹识别为一个机器人"
  exit
}

$now = Get-Date
ps python | foreach {
  $a, $b, $name = $_.CommandLine.split(' ')
  if ($name -and $bots.Contains("$name") -and (!$venv -or $a.Contains(".venv")) ) {
    # $_ | format-list *
    $bot = $bots["$name"]
    $bot.pid = $_.id
    $bot.status = $bot.pid -gt 0
    $bot.start = $_.StartTime
    $ago = (New-TimeSpan -Start $bot.start -End $now)
    Switch ($ago.TotalSeconds) {
      {$_ -gt 3600*24} { $bot.ago = $ago.ToString("d' days 'h' hours'") }
      {$_ -gt 3600} { $bot.ago = $ago.ToString("h' hours 'm' minutes'") }
      {$_ -gt 60} { $bot.ago = $ago.ToString("m' minutes 's' seconds'") }
      default { $bot.ago = $ago.ToString("s' seconds'") }
    }
  }
}

function status() {
  $color = @("Red", "Green")
  $statusText = @("Inactive (dead)", "Active (running)")
  foreach ($i in $bots.keys) { 
    $ai = $bots[$i]
    write-host -f $color[$ai.status] "●" -NoNewline
    write-host " $($ai.name)" -NoNewline
    write-host ("{0,23}" -f $statusText[$ai.status]) -f $color[$ai.status] -NoNewline
    write-host (" since {0}, {1} ago" -f ($bot.start, $bot.ago))
    write-host (" {0,9}   {1,-20}" -f ("PID:", $ai.pid))
    write-host (" {0,9}   {1,-20}" -f ("Command:", "python main.py"))
    write-host
  }
}

function stop() {
  param(
    [string]$bot_name
  )
  if (!$bot_name) {
    echo "用法: $0 stop <bot_name>"
    return
  }
  $bot = $bots[$bot_name]
  if (!$bot.status) {
    echo "$bot_name 未启动"
    return
  }
  kill $bot.pid
  echo "关闭机器人 $bot_name (pid: $($bot.pid))"
  $bot.pid = 0
  $bot.status = $false
}

function _start() {
  param(
    [string]$bot_name
  )
  if (!$bot_name) {
    echo "用法: $0 start <bot_name>"
    return
  }
  $bot = $bots[$bot_name]
  if ($bot.status) {
    echo "$bot_name 已经在运行了"
    return
  }

  $envpath = "$($bot_name)\.env"
  echo "读取 $envpath"
  [Environment]::SetEnvironmentVariable("BOT_HOME", $bot_name)
  Get-Content $envpath -Encoding utf8 | foreach {
    $name, $value = $_.split('=')
    if (!([string]::IsNullOrWhiteSpace($name)) -and !($name.Contains('#'))) {
      [Environment]::SetEnvironmentVariable($name.trim(), $value.trim())
    }
  }
  if ($venv){
    $runFilePath = ".venv\Scripts\python.exe"
  }else{
    $runFilePath = "python.exe"
  }
  $p = Start-Process -FilePath $runFilePath -ArgumentList @(".\main.py","$($bot.name)") -WindowStyle Hidden -PassThru -RedirectStandardOutput "$($bot_name)/bot.log" -RedirectStandardError "$($bot.name)/bot_error.log"
  echo "运行机器人 $($bot.name) (pid: $($p.id))"
}

function restart() {
  param(
    [string]$bot_name
  )
  if (!$bot_name) {
    echo "用法: $0 restart <bot_name>"
    return
  }
  $bot = $bots[$bot_name]
  if ($bot.status) {
    stop $bot_name
  }
  _start $bot_name
}

Switch ($1) {
  "status" { status; break }
  "start" { _start $bot_name; break }
  "restart" { 
    restart $bot_name
    break 
  }
  "stop" { stop $bot_name; break }
  "log" { log; break }
  default { echo "用法: $0 {start|restart|stop|status|log}" }
}

