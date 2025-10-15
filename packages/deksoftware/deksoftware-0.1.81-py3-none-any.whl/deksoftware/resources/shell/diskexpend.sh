#!/bin/bash

# Refs:
# https://qiita.com/hirofumihida/items/31371bf4124f5bf3305e
# https://www.rodolfocarvalho.net/blog/resize-disk-vagrant-libvirt/
# https://unix.stackexchange.com/a/583544

# Usage:
# self.sh /dev/vda /

DEV_DETAIL="$1"
PATH_TARGET="$2"

DEV_DETAIL_INDEX=$(fdisk -l | grep "$DEV_DETAIL" | awk 'END{print $1}' | cut -c $(( ${#DEV_DETAIL} + 1 ))-)

echo ", +" | sudo sfdisk -N "$DEV_DETAIL_INDEX" "$DEV_DETAIL" --no-reread
partprobe
pvresize "$DEV_DETAIL""$DEV_DETAIL_INDEX"
lvextend -r -l +100%FREE "$(mount | awk -v x="$PATH_TARGET" '$3 == x{print $1}')"
