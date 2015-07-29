#!/usr/bin/env bash

run_test() {
for rate in 300 500 700 800 1000
do
    for try in `seq 1 3`
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


#remove all delays in case they exist
ssh mininet@192.168.56.104 "sudo tc qdisc del dev eth1 root netem"
ssh mininet@192.168.56.101 "sudo tc qdisc del dev eth1 root netem"
ssh mininet@192.168.56.102 "sudo tc qdisc del dev eth1 root netem"


#run tests!
#mkdir -p /home/hassib/workspace/Evaluation
#run_test
#mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_nodelay
#sleep 10


mkdir -p /home/hassib/workspace/Evaluation
ssh mininet@192.168.56.104 "sudo tc qdisc add dev eth1 root netem delay 10ms"
ssh mininet@192.168.56.101 "sudo tc qdisc add dev eth1 root netem delay 10ms"
sleep 2
run_test
mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_prx10ms_sw5ms
ssh mininet@192.168.56.104 "sudo tc qdisc del dev eth1 root netem"
ssh mininet@192.168.56.101 "sudo tc qdisc del dev eth1 root netem"
sleep 10


#mkdir -p /home/hassib/workspace/Evaluation
#ssh mininet@192.168.56.104 "sudo tc qdisc add dev eth1 root netem delay 5ms"
#ssh mininet@192.168.56.101 "sudo tc qdisc add dev eth1 root netem delay 10ms"
#sleep 2
#run_test
#mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_prx5ms_sw10ms
#ssh mininet@192.168.56.104 "sudo tc qdisc del dev eth1 root netem"
#ssh mininet@192.168.56.101 "sudo tc qdisc del dev eth1 root netem"
#sleep 10


#mkdir -p /home/hassib/workspace/Evaluation
#ssh mininet@192.168.56.102 "sudo tc qdisc add dev eth1 root netem delay 10ms"
#sleep 2
#run_test
#mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_ditraone10ms
#ssh mininet@192.168.56.102 "sudo tc qdisc del dev eth1 root netem"
#sleep 10


#mkdir -p /home/hassib/workspace/Evaluation
#sudo tc qdisc add dev vboxnet1 root netem delay 10ms
#sleep 2
#run_test
#mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_ditratwo10ms
#sudo tc qdisc del dev vboxnet1 root netem
#sleep 10


#mkdir -p /home/hassib/workspace/Evaluation
#ssh mininet@192.168.56.104 "sudo tc qdisc add dev eth1 root netem delay 10ms"
#ssh mininet@192.168.56.101 "sudo tc qdisc add dev eth1 root netem delay 5ms"
#ssh mininet@192.168.56.102 "sudo tc qdisc add dev eth1 root netem delay 10ms"
#sleep 2
#run_test
#mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_prx10ms_sw5ms_ditraone10ms
#ssh mininet@192.168.56.104 "sudo tc qdisc del dev eth1 root netem"
#ssh mininet@192.168.56.101 "sudo tc qdisc del dev eth1 root netem"
#ssh mininet@192.168.56.102 "sudo tc qdisc del dev eth1 root netem"
#sleep 10


#mkdir -p /home/hassib/workspace/Evaluation
#ssh mininet@192.168.56.104 "sudo tc qdisc add dev eth1 root netem delay 5ms"
#ssh mininet@192.168.56.101 "sudo tc qdisc add dev eth1 root netem delay 10ms"
#ssh mininet@192.168.56.102 "sudo tc qdisc add dev eth1 root netem delay 10ms"
#sleep 2
#run_test
#mv /home/hassib/workspace/Evaluation /home/hassib/workspace/Evaluation_prx5ms_sw10ms_ditraone10ms
#ssh mininet@192.168.56.104 "sudo tc qdisc del dev eth1 root netem"
#ssh mininet@192.168.56.101 "sudo tc qdisc del dev eth1 root netem"
#ssh mininet@192.168.56.102 "sudo tc qdisc del dev eth1 root netem"
#sleep 10
