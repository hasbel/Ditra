for rate in `seq 100 100 1000`
do
    for try in `seq 1 100`
    do
        ssh mininet@192.168.56.105 "sudo timeout 60 python -u /home/mininet/oftest_hf/oft_ou.py -r ${rate} -d 40 &>> /dev/null &"
        sleep 1
        ssh mininet@192.168.56.105 'bash -s' < remote.sh
        sleep 1
        echo "rate ${rate} try ${try}: " >> /home/hassib/workspace/Evaluation/loss.log
        timeout 50 python -u sdnproxy/sdnproxy.py > /dev/null &
        timeout 25 python -u ditra.py >> /home/hassib/workspace/Evaluation/loss.log &
        sleep 20
        timeout 25 python -u ditra_migrate.py
        sleep 10
        rm -f /home/hassib/capture*
        scp mininet@192.168.56.105:/home/mininet/capture /home/hassib/
        python plot.py >> /home/hassib/workspace/Evaluation/loss.log
        sleep 2
        echo >> /home/hassib/workspace/Evaluation/loss.log
        mv /home/hassib/capture /home/hassib/workspace/Evaluation/capture${rate}_${try}
        mv /home/hassib/capture.png /home/hassib/workspace/Evaluation/capture${rate}.${try}.png
        sleep 10
    done
done
