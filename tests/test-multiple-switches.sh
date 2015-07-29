#!/usr/bin/env bash

for rate in 1000
do
    for try in `seq 1 5`
    do
        ssh mininet@192.168.56.105 "sudo timeout 40 python -u /home/mininet/oftest_hf/oft_ou.py -r ${rate} -d 20 &>> /dev/null &"
        ssh mininet@192.168.56.105 'bash -s' < remote.sh
        ssh mininet@192.168.56.103 "sudo timeout 40 python -u /home/mininet/oftest_hf/oft_ou.py -r ${rate} -d 20 &>> /dev/null &"
        ssh mininet@192.168.56.103 'bash -s' < remote.sh
        ssh mininet@192.168.56.106 "sudo timeout 40 python -u /home/mininet/oftest_hf/oft_ou.py -r ${rate} -d 20 &>> /dev/null &"
        ssh mininet@192.168.56.106 'bash -s' < remote.sh
        sleep 2
        ssh mininet@192.168.56.104 timeout 40 python -u /home/mininet/sdnproxy.py & #> /dev/null &
        sleep 1
        ssh mininet@192.168.56.102 timeout 15 python -u /home/mininet/Ditra/ditra.py >> /home/hassib/workspace/Evaluation/loss.log &
        sleep 10
        echo "rate ${rate} try ${try}: " >> /home/hassib/workspace/Evaluation/loss.log
        timeout 15 python -u ditra.py >> /home/hassib/workspace/Evaluation/loss.log
        sleep 10
        rm -f /home/hassib/capture*
        scp mininet@192.168.56.105:/home/mininet/capture /home/hassib/capture_oft1
        scp mininet@192.168.56.103:/home/mininet/capture /home/hassib/capture_oft2
        scp mininet@192.168.56.106:/home/mininet/capture /home/hassib/capture_oft3
        #python plot.py >> /home/hassib/workspace/Evaluation/loss.log
        #sleep 2
        echo >> /home/hassib/workspace/Evaluation/loss.log
        mv /home/hassib/capture_oft1 /home/hassib/workspace/Evaluation/capture_oft1_${rate}_${try}
        mv /home/hassib/capture_oft2 /home/hassib/workspace/Evaluation/capture_oft2_${rate}_${try}
        mv /home/hassib/capture_oft3 /home/hassib/workspace/Evaluation/capture_oft3_${rate}_${try}
        #mv /home/hassib/capture /home/hassib/workspace/Evaluation/capture${rate}_${try}
        #mv /home/hassib/capture.png /home/hassib/workspace/Evaluation/capture${rate}_${try}.png
        sleep 10
    done
done

