#!/bin/bash
root=$(dirname $(realpath $0))
bots=()

for i in $root/*; do
  if [ -d "$i" ]; then 
    if [ -f "$i/.env" ]; then
      bots[${#bots[@]}]=$(basename "$i")
    fi
  fi
done

color=("\e[31m" "\e[32m")
status_text=("Died" "Runing")

pid=()
status=()
start_time=()

for i in ${!bots[@]}; do
  bot=${bots[$i]}
  p=$(ps aux | grep "$root" | grep "bot'$bot'" | grep -v grep | awk '{print $2}')
  pid[$i]=$p
  status[$i]=0
  start_time[$i]=""
  if [[ ! -z "$p" ]]; then
    status[$i]=1
    start_time[$i]=$(ps -p $p -o lstart | sed -n '2p')
  fi
done


_status(){
  for i in ${!bots[@]}; do
    s=${status[$i]}
    printf ${color[$s]}
    printf "●"
    printf "\e[0m"
    printf " ${bots[$i]}   " 
    printf ${color[$s]}
    printf ${status_text[$s]}
    printf "\e[0m\n"
    
    printf "%10s %s\n" PID "${pid[$i]}"
    printf "%10s %s\n" Since "${start_time[$i]}"
  done
}

_stop(){
  b=-1
  for i in ${!bots[@]}; do
    if [ "$1" = "${bots[$i]}" ]; then
      b=$i
    fi
  done
  if [ $b -eq -1 ]; then 
    echo 'bot "'"$1"'" 不存在.'
    exit 1
  fi
  if [ ${status[$b]} -eq 0 ]; then
    echo "机器人未启动"
  else
    p=${pid[$b]}
    kill $p
    echo "杀死进程 $p"
    pid[$b]=0
    status[$b]=0
    start_time[$b]=""
  fi
}

_start(){
  b=-1
  for i in ${!bots[@]}; do
    if [ "$1" = "${bots[$i]}" ]; then
      b=$i
    fi
  done
  if [ $b -eq -1 ]; then 
    echo 'bot "'"$1"'" 不存在.'
    exit 1
  fi
  bot=${bots[$b]}
  if [ ${status[$b]} -gt 0 ]; then
    echo "机器人 $bot 已经正在运行啦"
  else
    cd $root && nohup python $root/main.py "$bot" "bot'$bot'" > $root/$bot/bot.log 2>&1 &
    echo "启动机器人 $bot 中..."
  fi
}

case $1 in
  start|stop|restart|log)
    bot=$2
    if [ -z "$bot" ]; then
      echo "未从参数中读取到机器人名"
      if [ ${#bots[@]} -eq 1 ]; then
        bot=${bots[0]}
        echo "自动选择唯一机器人 \"$bot\""
      else
       for i in ${!bots[@]}; do
          printf "  %d. %s\n" $i "${bots[$i]}"
        done
        read  -p "请输入需要序号: " b
        if [ -z "$b" ] || [ -z "${bots[$b]}" ]; then
          echo "输入错误"
          exit 1
        fi
        bot=${bots[$b]}
      fi
      
    fi
    ;;
esac
case $1 in
  start)
    _start $bot
    ;;
  stop)
    _stop $bot
    ;;
  restart)
    _stop $bot
    _start $bot
    ;;
  status)
    _status
    ;;
  log)
    cat $root/$bot/bot.log | tail -n 100
    ;;
  ps)
    ps aux | grep python | grep -v grep
    ;;
  *)
    echo "Usage: $0 start|stop|status|log"
esac