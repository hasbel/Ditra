import matplotlib.pyplot as plt


def parse_capture(
        path="/home/hassib/capture", plot=False, xlim=None, ylim=None,
        switch_migration_xid=None, ctrl_migration_xid=None):
    f = open (path)
    request_dict = {}
    reply_dict = {}
    latency_dict = {}
    duplicated_packets = []
    lost_packets = []
    loss = 0
    duplication = 0
    for line in f:
        line = line[:-1]
        # register packet time and remove it from line
        separator = line.index(",")
        packet_time = line[:separator]
        line = line[(separator+1):]
        #determine if line contains requests or replies
        if line[0] == ",":
            # we have replies, get reply id
            replies = line[1:].split(",")
            for reply in replies:
                if reply:
                    reply_xid = int(reply)
                    if reply_xid in reply_dict:
                        duplication += 1
                        duplicated_packets.append(reply_xid)
                    else:
                        reply_dict[reply_xid] = packet_time
        else:
            # we have requests, get request id
            requests = line.split(",")
            for request in requests:
                if request:
                    request_xid = int(request)
                    request_dict[request_xid] = packet_time

    for xid in request_dict.keys():
        if xid in reply_dict:
            if xid < 200000:
                latency = float(reply_dict[xid]) - float(request_dict[xid])
                #if latency > 0.011:
                 #   latency = 0.011
                latency_dict[xid] = latency
        else:
            loss += 1
            lost_packets.append(xid)
    if plot:
        print "loss: %i" % loss
        if loss:
            print "Lost packets: ", lost_packets
        print "duplication: %i" % duplication
        if duplication:
            print "Duplicated packets: ", duplicated_packets
        plt.clf()
        plt.plot(latency_dict.keys(), latency_dict.values())
        if switch_migration_xid:
            plt.plot(switch_migration_xid, latency_dict[switch_migration_xid], "rx")
        if ctrl_migration_xid:
            plt.plot(ctrl_migration_xid, latency_dict[ctrl_migration_xid], "gx")
        plt.ylabel('Latency')
        plt.xlabel('xid')
        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.savefig(path+'.png', bbox_inches='tight')
    else:
        return latency_dict


def plot_migration_window():
    capture_path = "/home/hassib/capture"
    switch_migration_xid = None
    controller_migration_xid = None
    log = open("/home/hassib/workspace/Evaluation/loss.log")
    log = list(log)[-2:]
    f = open(capture_path)
    if f.read() == "":
        pass
    else:
        for line in log:
            if "Switch migrated:" in line:
                switch_migration_xid = int(line[17:])
            elif "Controller migrated:" in line:
                controller_migration_xid = int(line[21:])
        if switch_migration_xid > controller_migration_xid:
            parse_capture(path=capture_path, plot=True,
                          xlim=[controller_migration_xid-100, switch_migration_xid+100],
                          ctrl_migration_xid=controller_migration_xid,
                          switch_migration_xid=switch_migration_xid)
        else:
            parse_capture(path=capture_path, plot=True,
                          xlim=[switch_migration_xid-100, controller_migration_xid+100],
                          ctrl_migration_xid=controller_migration_xid,
                          switch_migration_xid=switch_migration_xid)

# def plot_migration_window_for_all():
#     log = open("/home/hassib/workspace/Evaluation40/loss.log")
#     log = list(log)
#     for rate in range(100,701,100):
#         for run in range(1,41):
#             capture_path = ("/home/hassib/workspace/Evaluation40/capture" +
#                             str(rate) + "_" + str(run))
#             f = open(capture_path)
#             if f.read() == "":
#                 pass
#             else:
#                 xid_line = log[log.index("rate %i try %i: \n" % (rate, run)) + 1]
#                 xid = int(xid_line[xid_line.index(":")+1:])
#                 parse_capture(path=capture_path,plot=True, xlim=[xid-100,xid+100])
#
#
# def plot_average(rate,runs=100):
#     all_latencies = []
#     final_latency_dict = {}
#     for run in range(1,runs+1):
#         path = "/home/hassib/workspace/Evaluation/capture" + str(rate) + "_" + str(run)
#         latency_dict = parse_capture(path)
#         all_latencies.append(latency_dict)
#     for xid in range(100,(rate*40)+100):
#         xid_latency_sum = 0
#         for latency_dict in all_latencies:
#             try: # accounting for lost packets
#                 xid_latency_sum += latency_dict[xid]
#             except KeyError:
#                 xid_latency_sum += latency_dict[xid-1]
#         final_latency_dict[xid] = xid_latency_sum / runs
#     plt.plot(final_latency_dict.keys(), final_latency_dict.values())
#     plt.ylabel('Latency')
#     plt.xlabel('xid')
#     plt.ylim([0,0.010])
#     plt.savefig("/home/hassib/average"+str(rate)+".png", bbox_inches='tight')
#
#
# def plot_loss():
#     loss = {}
#     f = open ("/home/hassib/workspace/Evaluation/loss.log")
#     data = list(f)
#     for line in data:
#         if "rate " in line:
#             rate = int(line[5:9])
#             if "Migration: " in data[data.index(line)+1]:
#                 if rate in loss:
#                     loss[rate] += int (data[data.index(line)+2][5:7])
#                 else:
#                     loss[rate] = int(data[data.index(line)+2][5:7])
#             else:
#                 pass #ignore corrupted  data
#     plt.plot(loss.keys(), loss.values(), "bo")
#     plt.ylim([0,11])
#     plt.ylabel('chance of one packet being lost [%]')
#     plt.xlim([0,1100])
#     plt.xlabel('data rate [msg/s]')
#     plt.show()

if __name__ == "__main__":
    #parse_capture(plot=True)
    plot_migration_window()
    #plot_average(rate=100)
    #plot_loss()
