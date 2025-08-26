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
  p=$(ps aux | grep "$root" | grep "bot'$bot'" | grep -v grep | grep -v ps | grep -v sh | awk '{print $2}')
  pid[$i]=$p
  status[$i]=0
  start_time[$i]=""
  if [[ ! -z "$p" ]]; then
    status[$i]=1
    start_time[$i]=$(ps -p $p -o lstart | sed -n '2p')
  fi
done

# 代码补全
cat > /etc/bash_completion.d/tgbot.bash << EOF
_foo() 
{
  COMPREPLY=()
  local cur=\${COMP_WORDS[COMP_CWORD]}
  local cmd=\${COMP_WORDS[COMP_CWORD-1]}
  case "\$cmd" in
    'tgbot')
      COMPREPLY=( \$(compgen -W 'status start stop restart log ps' -- \$cur) ) 
      ;;
    'start' | 'stop' | 'restart' | 'log')
      COMPREPLY=( \$(compgen -W '${bots[@]}' -- \$cur) ) 
      ;;
    '*')
      ;;
  esac
  return 0
}
complete -F _foo tgbot
EOF
cat > "$HOME/.config/fish/completions/tgbot.fish" << EOF
complete -x -c tgbot -n "not __fish_seen_subcommand_from start; and not __fish_seen_subcommand_from restart; and not __fish_seen_subcommand_from stop; and not __fish_seen_subcommand_from log" -a "status start stop restart log ps"
complete -x -c tgbot -n "__fish_seen_subcommand_from start" -a "${bots[@]}"
complete -x -c tgbot -n "__fish_seen_subcommand_from stop" -a "${bots[@]}"
complete -x -c tgbot -n "__fish_seen_subcommand_from restart" -a "${bots[@]}"
complete -x -c tgbot -n "__fish_seen_subcommand_from log" -a "${bots[@]}"
EOF

show() {
  for i in ${!_array[@]}; do
    if [ $i -eq $index ]; then
      printf $'\033[30;47m  %d. %s \033[0m\n' "$i" "${_array[$i]}"
    else
      printf "\x1b[0m  %d. %s \n" $i "${_array[$i]}"
    fi
  done
}
choose() {
  _array=()
  for i in "$@"; do 
    _array[${#_array[@]}]="$i"
  done
  text="0"
  backspace=0
  control=0
  control_text=""
  index=0
  show 
  echo -n '请输入序号: 0'
  while IFS= read -s -n 1 char; do
    if [[ "$char" == $'\x08' ]] || [[ "$char" == $'\x7f' ]]; then
      text="${text%?}"
      backspace=1
    elif [[ "$char" == $'\r' ]] || [[ "$char" == $'\n' ]] || [[ -z "$char" ]]; then
      echo
      break
    elif [[ "$char" == $'\x1b' ]]; then
      control=1
    elif [[ -n "$char" ]]; then
      if [[ control -eq 0 ]] && [[ "$char" =~ ^[0-9]+$ ]] && [[ ${#text} -lt 2 ]]; then
        text="$text""$char"
      else
        control_text="$control_text""$char"
      fi
      if [[ ${#control_text} -eq 2 ]]; then
        if [[ $control_text == '[A' ]]; then
          if [ $index -gt 0 ]; then
            index=$(($index - 1))
          else
            index=$((${#_array[@]} - 1))
          fi
        elif [[ $control_text == '[B' ]]; then
          if [ "$index" -lt $((${#_array[@]} - 1)) ]; then
            index=$(($index + 1))
          else 
            index="0"
          fi
        fi
        text="$index"
        control=0
        control_text=""
      fi
    fi
    if [ -n "$text" ]; then 
      tindex=$(("10#""$text"))
      if [ $tindex -ge 0 ] && [ $tindex -lt ${#_array[@]} ]; then
        index=$tindex
      fi
    fi
    printf '\r'
    for (( i=0; i<${#_array[@]}; i++)); do 
      printf $'\x1b[A'
    done
    show 
    if [ -n "$text" ]; then
      printf "\r请输入序号: %s \x1b[D" "$text"
    else
      printf "\r请输入序号: %s \x1b[D" "$index"
    fi
    if [[ $backspace -eq 1 ]]; then
      if [ ${#text} -eq 1 ]; then
        printf "\x1b[C\x1b[D\x1b[K"
      else
        printf "\x1b[D\x1b[K"
      fi
      backspace=0
    fi
  done
  return $index
}


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
    kill -s SIGINT "$p"
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

action="$1"
if [ -z "$action" ]; then
  echo "未从参数中读取到操作名"
  actions=(status start stop restart log ps)
  choose "${actions[@]}"
  action=${actions[$?]}
fi

case $action in
  start|stop|restart|log)
    bot=$2
    if [ -z "$bot" ]; then
      echo "未从参数中读取到机器人名"
      if [ ${#bots[@]} -eq 1 ]; then
        bot=${bots[0]}
        echo "自动选择唯一机器人 \"$bot\""
      else
        choose "${bots[@]}"
        bot=${bots[$?]}
      fi
 
    fi
    ;;
esac
case $action in
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
    num=100
    if [ -n "$3" ]; then 
      num=$3
    fi
    # printf "$(tail -n $num $root/$bot/bot.log | sed -e "s/\(.*\[DEBUG\].*\)/\\\e[35m\1\\\033[00m/g" -e "s/\(.*\[INFO\].*\)/\\\e[32m\1\\\033[00m/g" -e "s/\(.*\[WARNING\].*\)/\\\e[33m\1\\\033[00m/g" -e "s/\(.*\[ERROR\].*\)/\\\e[31m\1\\\033[00m/g" -e "s/\(.*\[CRITICAL\].*\)/\\\e[31;47m\1\\\033[00m/g")"
    printf "$(tail -n $num $root/$bot/bot.log | sed -e 's/\\/\\\\/g' -e "s/\[\(DEBUG\)\]/\[\\\e[35m\1\\\033[00m\]/g" -e "s/\[\(INFO\)\]/\[\\\e[32m\1\\\033[00m\]/g" -e "s/\[\(WARNING\)\]/\[\\\e[33m\1\\\033[00m\]/g" -e "s/\[\(ERROR\)\]/\[\\\e[31m\1\\\033[00m\]/g" -e "s/\[\(CRITICAL\)\]/\[\\\e[31;47m\1\\\033[00m\]/g")"
    ;;
  ps)
    ps aux | grep python | grep -v grep
    ;;
  *)
    echo "Usage: $0 <status|start|stop|restart|log|ps>"
    exit 1
esac
exit 0