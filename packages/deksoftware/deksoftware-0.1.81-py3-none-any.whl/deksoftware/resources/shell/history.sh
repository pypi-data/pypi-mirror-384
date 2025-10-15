#!/bin/bash

cat <<EOF | tee ~/.inputrc
"\e[A": history-search-backward
"\e[B": history-search-forward
EOF
#bind -f  ~/.inputrc

rm -rf ~/.bash_history
history -c
