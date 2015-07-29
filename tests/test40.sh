#!/usr/bin/env bash

run_test() {
for rate in `seq 500 100 1000`
do
    for try in `seq 1 40`
    do
        ssh mininet@192.168.56.105 "sudo timeout 40 python -u /home/mininet/oftest_hf/oft_ou.py -r ${rate} -d 20 &>> /dev/null &"
        ssh mininet@192.168.56.105 'bash -s' < remote.sh
        sleep 2
        ssh mininet@192.168.56.104 timeout 40 python -u /home/mininet/sdnproxy.py > /dev/null &
        sleep 1
        ssh mininet@192.168.56.102 timeout 15 python -u /home/mininet/Ditra/ditra.py >> /home/hassib/workspace/Evaluation/loss.log &
        sleep 10
        echo "rate ${rate} try ${try}: " >> /home/hassib/workspace/Evaluation/loss.log
        timeout 15 python -u ditra.py >> /home/hassib/workspace/Evaluation/loss.log
        sleep 14
        rm -f /home/hassib/capture*
        scp mininet@192.168.56.105:/home/mininet/capture /home/hassib/
        python plot.py >> /home/hassib/workspace/Evaluation/loss.log
        sleep 2
        echo >> /home/hassib/workspace/Evaluation/loss.log
        mv /home/hassib/capture /home/hassib/workspace/Evaluation/capture${rate}_${try}
        mv /home/hassib/capture.png /home/hassib/workspace/Evaluation/capture${rate}_${try}.png
        mv /home/hassib/capture.pdf /home/hassib/workspace/Evaluation/capture${rate}_${try}.pdf
        sleep 10
    done
done
}

mkdir -p /home/hassib/workspace/Evaluation
run_test
mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation40_3
sleep 10

