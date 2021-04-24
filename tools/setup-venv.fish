#!/usr/bin/env fish

set py39_path (which python3.9)

if test -n "$py39_path"
    echo "python3.9 is installed"
else
    echo "installing python3.9, sudo is required..."
    sudo apt update
    sudo apt install software-properties-common
    if not ls "/etc/apt/sources.list.d/" | grep deadsnakes
       echo "adding apt repository for python3.9"
       sudo add-apt-repository ppa:deadsnakes/ppa
    end
    sudo apt install python3.9
    sudo apt install python3.9-venv
    sudo apt install python3.9-distutils
end

set -l root_dir (git rev-parse --show-toplevel)
set -l env_dir $root_dir/python-venv
echo "setting up venv: $env_dir"
python3.9 -m venv $env_dir
source $env_dir/bin/activate.fish
python3.9 -m pip install -r $root_dir/requirements.txt

