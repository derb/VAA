#!/bin/bash
#MAC only

NODES=$(grep -c '' config)

function new_tab() {
  TAB_NAME=$1
  COMMAND=$2
  osascript \
    -e "tell application \"Terminal\"" \
    -e "tell application \"System Events\" to keystroke \"t\" using {command down}" \
    -e "do script \"printf '\\\e]1;$TAB_NAME\\\a'; $COMMAND\" in front window" \
    -e "end tell" > /dev/null
}

for i in $(seq 1 1 $NODES)
  do
    new_tab "Node $i" "python Node.py $i"
  done
