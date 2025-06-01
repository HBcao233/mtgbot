#!/bin/bash
root=$(dirname $(realpath $0))

color=("\e[31m" "\e[32m")
status_text=("Died" "Runing")

pid=$(ps -ef | grep "$root" | grep -v grep | awk '{print $2}')
status=0
start_time=""
if [[ ! -z "$pid" ]]; then
  status=1
  start_time=$(ps -p $pid -o lstart | sed -n '2p')
fi

_status(){
  printf ${color[$status]}
  printf "●"
  printf "\e[0m"
  printf " mtgbot   " 
  printf ${color[$status]}
  printf ${status_text[$status]}
  printf "\e[0m\n"
  
  printf "%10s %s\n" PID $pid
  printf "%10s %s\n" Since "$start_time"
}

_stop(){
  if [ $status -eq 0 ]; then
    echo "机器人未启动"
  else
    kill $pid
    echo "杀死进程 $pid"
    pid=""
    status=0
    start_time=""
  fi
}

_start(){
  if [ $status -gt 0 ]; then
    echo "机器人已经正在运行啦"
  else
    nohup python $root/main.py > $root/bot.log 2>&1 &
    echo "启动机器人中..."
  fi
}

case $1 in
  start)
    _start
    ;;
  stop)
    _stop
    ;;
  restart)
    _stop 
    _start
    ;;
  status)
    _status
    ;;
  log)
    cat $root/bot.log | tail -n 100
    ;;
  *)
    echo "Usage: $0 start|stop|status|log"
esac