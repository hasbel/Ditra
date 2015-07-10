import matplotlib.pyplot as plt

def old_parser():
    f = open("/home/hassib/latency.log")
    latency_table = []
    xid_table = []
    for line in f:
        if line:
            separator = line.index(":")
            latency_table.append(float(line[(separator+1):]))
            xid_table.append(int(line[:separator]))
    plt.plot(xid_table, latency_table)
    plt.ylabel('some numbers')
    plt.show()

def parse_capture():
    f = open ("/home/hassib/capture")
    request_dict = {}
    reply_dict = {}
    latency_dict = {}
    loss = 0
    duplication = 0
    for line in f:
        line = line[:-1]
        # get time
        separator = line.index(",")
        packet_time = line[:separator]
        # get request xid
        line = line[(separator+1):]
        separator = line.index(",")
        request_xid = line[:separator]
        if request_xid:
            request_dict[int(request_xid)] = packet_time
        # get reply xid
        reply = line[(separator+1):]
        if reply:
            try:
                # check if multiple reply got bundled together
                while reply:
                    comma = reply.index(",")
                    reply_xid = int(reply[:comma])
                    if reply_xid in reply_dict:
                        duplication += 1
                    else:
                        reply_dict[reply_xid] = packet_time
                    reply = reply[comma+1:]
            except:
                reply_dict[int(reply)] = packet_time
    for xid in request_dict.keys():
        if xid in reply_dict:
            if xid < 200000:
                latency_dict[xid] = float(reply_dict[xid]) - float(request_dict[xid])
        else:
            loss += 1

    print "loss: %i" % loss
    print "duplication: %i" % duplication
    plt.plot(latency_dict.keys(), latency_dict.values())
    plt.ylabel('Latency')
    plt.xlabel('xid')
    plt.ylim([0,0.010])
    plt.savefig('/home/hassib/capture.png', bbox_inches='tight')

if __name__ == "__main__":
    parse_capture()
