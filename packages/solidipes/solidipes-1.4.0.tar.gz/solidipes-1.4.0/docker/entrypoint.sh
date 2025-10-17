#!/bin/bash

ARGS=$(eval echo $@)

root_dir=$(echo "$ARGS" | awk -F'--ServerApp.root_dir=' '{print $2}' | awk '{print $1}')
root_dir="${root_dir:-$PWD}"
echo "Root dir: $root_dir"

if test -f "$root_dir/pkg.txt"; then
    sudo apt update
    sudo DEBIAN_FRONTEND=noninteractive apt install -y $(cat $root_dir/pkg.txt)
fi

if test -f "$root_dir/requirements.txt"; then
    pip install -r $root_dir/requirements.txt
fi

if test -f "$root_dir/bashrc.sh"; then
    source $root_dir/bashrc.sh
fi

if test -f "$root_dir/bashrc"; then
    source $root_dir/bashrc
fi

sudo rm -f /etc/sudoers.d/apt

if test $FILEBROWSER_BASEURL; then
    echo "Env filebrowser base url: $FILEBROWSER_BASEURL"
else
    export FILEBROWSER_BASEURL=$RENKU_BASE_URL_PATH/filebrowser
fi
echo "Setting filebrowser base url: $FILEBROWSER_BASEURL"
echo $FILEBROWSER_BASEURL >/tmp/filebrowser_baseurl

if test $WEBDAV_BASEURL; then
    echo "Env webdav base url: $WEBDAV_BASEURL"
else
    export WEBDAV_BASEURL=$RENKU_BASE_URL_PATH/webdav
fi
echo "Setting webdav base url: $WEBDAV_BASEURL"
echo $WEBDAV_BASEURL >/tmp/webdav_baseurl

echo $root_dir >/tmp/root_dir

export DISPLAY=:99.0
export PYVISTA_OFF_SCREEN=true
export PYVISTA_PLOT_THEME=document
which Xvfb
Xvfb :99 -screen 0 1024x768x24 >/dev/null 2>&1 &
sleep 3
env

jupyter() {
    if [ "$1" = "notebook" ]; then
        shift
        $(which jupyter) server $@
    else
        $(which jupyter) $@
    fi
}
source /etc/profile.d/env-vars.sh
echo $NOTEBOOK_OPTION
eval echo $NOTEBOOK_OPTION
eval echo $@
echo $ARGS
echo "Execute command: $@ $NOTEBOOK_OPTION"

cd $root_dir
$ARGS $NOTEBOOK_OPTION
