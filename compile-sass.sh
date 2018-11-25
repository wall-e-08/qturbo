#!/bin/bash

# run this script to compile scss to css for this project

# install sass: sudo apt-get install ruby-sass
# for short doc: sass -h

RED='\033[0;31m'
LGREEN='\033[1;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [[ "$1" ]]; then
    printf "${LGREEN}SCSS folder location: ${CYAN}$1${NC}\n"
    if [[ "$2" == "-c" ]]; then
        sass --watch $1/scss:$1/css --no-cache --style compressed
    else
        sass --watch $1/scss:$1/css --no-cache --style expanded
    fi
else
    printf "\n ---> Please enter ${YELLOW}SCSS folder location${NC} location in 1st argument\n"
    printf " ---> Example: ${LGREEN}./compile-sass.sh ${CYAN}packages/<app-name>/static/<app-name>${NC}\n\n"
fi