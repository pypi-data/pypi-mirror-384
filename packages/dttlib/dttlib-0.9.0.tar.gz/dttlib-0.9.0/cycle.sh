#!/bin/bash
set -x

cmd="timeout $@"
echo $cmd
while true
do
    $cmd
    if [[ $? -ne 124 ]]
    then
	    break
    fi
    sleep 0.1
    echo "***********************************************"
done

