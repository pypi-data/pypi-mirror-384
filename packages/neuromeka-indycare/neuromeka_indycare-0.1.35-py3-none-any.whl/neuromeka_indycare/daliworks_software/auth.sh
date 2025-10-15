#!/bin/bash -p

# echo -e "\nexport TERM=xterm" >> ~/.bashrc
export TERM=xterm
source ~/.bashrc

read -p "User: " user
su --login $user
