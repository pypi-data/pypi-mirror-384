#!/bin/bash

set -e

not_in_array() {
    local needle="$1"
    shift 1
    local haystack=("$@")

    local value
    for value in "${haystack[@]}"; do
        [ "$value" = "$needle" ] && return 1
    done
    return 0
}


if [ "$(id -u)" -eq 0 ]; then

if hash apt-get 2>/dev/null; then
  if lsb_release -a | grep Ubuntu; then
      if [ -f "/usr/share/doc/apt/examples/sources.list" ]; then
        mkdir -p /etc/apt
        cp -rf /usr/share/doc/apt/examples/sources.list /etc/apt/sources.list
      fi
      if [ -f "/etc/apt/sources.list" ]; then
        sed -i "s@http://.*archive.ubuntu.com@http://mirrors.tuna.tsinghua.edu.cn@g" /etc/apt/sources.list
        sed -i "s@http://.*security.ubuntu.com@http://mirrors.tuna.tsinghua.edu.cn@g" /etc/apt/sources.list
      fi
  fi
fi

if hash apt-get 2>/dev/null; then
  if lsb_release -a | grep Debian; then
    if [ -f "/etc/apt/sources.list.d/debian.sources" ]; then
      sed -i "s@http://.*deb.debian.org@http://mirrors.tuna.tsinghua.edu.cn@g" /etc/apt/sources.list.d/debian.sources
    fi
  fi
fi

if not_in_array docker "$@" ; then
if hash docker 2>/dev/null; then
mkdir -p /etc/docker
cat <<EOF | tee /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn",
    "https://docker.mirrors.sjtug.sjtu.edu.cn",
    "https://registry-1.docker.io"
  ]
}
EOF
systemctl daemon-reload && systemctl restart docker
fi
fi


## https://zhuanlan.zhihu.com/p/655419673
## https://github.com/ciiiii/cloudflare-docker-proxy
if not_in_array containerd "$@" ; then
if hash containerd 2>/dev/null; then
mkdir -p /etc/containerd
cat <<EOF | tee /etc/containerd/config.toml
version = 2

[plugins]
  [plugins."io.containerd.grpc.v1.cri"]
    [plugins."io.containerd.grpc.v1.cri".registry]
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
          endpoint = ["https://docker.1panel.live","https://docker.m.daocloud.io","https://dockerproxy.com","https://docker.nju.edu.cn","https://docker.mirrors.sjtug.sjtu.edu.cn","https://registry-1.docker.io"]
EOF
systemctl daemon-reload && systemctl restart containerd
fi
fi

if [ -f "/usr/share/zoneinfo/Asia/Shanghai" ]; then
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
fi

fi


if hash npm 2>/dev/null; then
  npm cache clean -f
cat <<EOF | tee $HOME/.npmrc
registry=http://registry.npmmirror.com
disturl=https://npmmirror.com/mirrors/node/
sharp_binary_host=https://npmmirror.com/mirrors/sharp
sharp_libvips_binary_host=https://npmmirror.com/mirrors/sharp-libvips
profiler_binary_host_mirror=https://npmmirror.com/mirrors/node-inspector/
fse_binary_host_mirror=https://npmmirror.com/mirrors/fsevents
node_sqlite3_binary_host_mirror=https://npmmirror.com/mirrors
sqlite3_binary_host_mirror=https://npmmirror.com/mirrors
sqlite3_binary_site=https://npmmirror.com/mirrors/sqlite3
sass_binary_site=https://npmmirror.com/mirrors/node-sass
electron_builder_binaries_mirror=https://npmmirror.com/mirrors/electron-builder-binaries/
electron_mirror=https://npmmirror.com/mirrors/electron/
electron_custom_dir="{{ version }}"
version=true
puppeteer_download_host=https://npmmirror.com/mirrors
chromedriver_cdnurl=https://npmmirror.com/mirrors/chromedriver
operadriver_cdnurl=https://npmmirror.com/mirrors/operadriver
phantomjs_cdnurl=https://npmmirror.com/mirrors/phantomjs
python_mirror=https://npmmirror.com/mirrors/python
EOF
#  npm config set registry http://registry.npmmirror.com
#  npm config set disturl https://npmmirror.com/mirrors/node/
#  npm config set sharp_binary_host https://npmmirror.com/mirrors/sharp
#  npm config set sharp_libvips_binary_host https://npmmirror.com/mirrors/sharp-libvips
#  npm config set profiler_binary_host_mirror https://npmmirror.com/mirrors/node-inspector/
#  npm config set fse_binary_host_mirror https://npmmirror.com/mirrors/fsevents
#  npm config set node_sqlite3_binary_host_mirror https://npmmirror.com/mirrors
#  npm config set sqlite3_binary_host_mirror https://npmmirror.com/mirrors
#  npm config set sqlite3_binary_site https://npmmirror.com/mirrors/sqlite3
#  npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass
#  npm config set electron_builder_binaries_mirror https://npmmirror.com/mirrors/electron-builder-binaries/
#  npm config set electron_mirror https://npmmirror.com/mirrors/electron/
#  npm config set electron_custom_dir "{{ version }}"
#  npm config set puppeteer_download_host https://npmmirror.com/mirrors
#  npm config set chromedriver_cdnurl https://npmmirror.com/mirrors/chromedriver
#  npm config set operadriver_cdnurl https://npmmirror.com/mirrors/operadriver
#  npm config set phantomjs_cdnurl https://npmmirror.com/mirrors/phantomjs
#  npm config set python_mirror https://npmmirror.com/mirrors/python
fi

## https://mirrors.cernet.edu.cn/list/pypi
PYPI_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
PYPI_INDEX_EXTRA_1=https://pypi.cnb.cool/deksep/common/-/packages/simple
PYPI_INDEX_EXTRA_2=https://mirror.nju.edu.cn/pypi/web/simple
PYPI_INDEX_EXTRA_3=https://mirror.sjtu.edu.cn/pypi/web/simple

if hash pip3 2>/dev/null; then
mkdir -p $HOME/.config/pip
cat <<EOF | tee $HOME/.config/pip/pip.conf
[global]
index-url = $PYPI_INDEX
extra-index-url = $PYPI_INDEX_EXTRA_1
;                 $PYPI_INDEX_EXTRA_2
;                 $PYPI_INDEX_EXTRA_3
EOF
fi

if hash pdm 2>/dev/null; then
  pdm config pypi.url $PYPI_INDEX
  pdm config pypi.extra.url $PYPI_INDEX_EXTRA_1
#  pdm config pypi.extra.url $PYPI_INDEX_EXTRA_2
#  pdm config pypi.extra.url $PYPI_INDEX_EXTRA_3
fi

if hash gem 2>/dev/null; then
  gem sources --add https://gems.ruby-china.com/ --remove https://rubygems.org/
fi
