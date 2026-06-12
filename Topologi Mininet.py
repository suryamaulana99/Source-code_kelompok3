from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def build():

    net = Mininet(
        controller=RemoteController,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False,
        autoStaticArp=False
    )

    print("*** Adding Controller")
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='<IP VM yang menjalankan RYU>',
        port=6653
    )

    print("*** Adding Spine Switches")
    s1 = net.addSwitch('s1', dpid='0000000000000001', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', dpid='0000000000000002', protocols='OpenFlow13')

    print("*** Adding Leaf Switches")
    s3 = net.addSwitch('s3', dpid='0000000000000003', protocols='OpenFlow13')
    s4 = net.addSwitch('s4', dpid='0000000000000004', protocols='OpenFlow13')
    s5 = net.addSwitch('s5', dpid='0000000000000005', protocols='OpenFlow13')
    s6 = net.addSwitch('s6', dpid='0000000000000006', protocols='OpenFlow13')

    print("*** Adding Hosts")
    h1 = net.addHost('h1', ip='192.168.10.11/24', mac='00:00:10:01:00:11')
    h2 = net.addHost('h2', ip='192.168.10.12/24', mac='00:00:10:01:00:12')
    h3 = net.addHost('h3', ip='192.168.10.21/24', mac='00:00:10:02:00:21')
    h4 = net.addHost('h4', ip='192.168.10.22/24', mac='00:00:10:02:00:22')
    h5 = net.addHost('h5', ip='192.168.10.31/24', mac='00:00:10:03:00:31')
    h6 = net.addHost('h6', ip='192.168.10.32/24', mac='00:00:10:03:00:32')
    h7 = net.addHost('h7', ip='192.168.10.41/24', mac='00:00:10:04:00:41')
    h8 = net.addHost('h8', ip='192.168.10.42/24', mac='00:00:10:04:00:42')

    print("*** Creating Link Parameters")
    host_link = dict(bw=10, delay='1ms', use_htb=True)
    spine_link = dict(bw=10, delay='2ms', use_htb=True)

    print("*** Connecting Hosts to Leaf Switches")
    net.addLink(h1, s3, port2=1, **host_link)
    net.addLink(h2, s3, port2=2, **host_link)
    net.addLink(h3, s4, port2=1, **host_link)
    net.addLink(h4, s4, port2=2, **host_link)
    net.addLink(h5, s5, port2=1, **host_link)
    net.addLink(h6, s5, port2=2, **host_link)
    net.addLink(h7, s6, port2=1, **host_link)
    net.addLink(h8, s6, port2=2, **host_link)

    print("*** Connecting Leaf to Spine")
    net.addLink(s3, s1, port1=3, port2=1, **spine_link)
    net.addLink(s3, s2, port1=4, port2=1, **spine_link)
    net.addLink(s4, s1, port1=3, port2=2, **spine_link)
    net.addLink(s4, s2, port1=4, port2=2, **spine_link)
    net.addLink(s5, s1, port1=3, port2=3, **spine_link)
    net.addLink(s5, s2, port1=4, port2=3, **spine_link)
    net.addLink(s6, s1, port1=3, port2=4, **spine_link)
    net.addLink(s6, s2, port1=4, port2=4, **spine_link)

    print("*** Starting Network")
    net.start()

    print("\n========== TOPOLOGY INFORMATION ==========")
    print("Controller : c0 (192.168.157.5:6653)")
    print("Spine      : s1, s2")
    print("Leaf       : s3, s4, s5, s6")
    print("------------------------------------------")
    print("h1 : 192.168.10.11  |  h2 : 192.168.10.12")
    print("h3 : 192.168.10.21  |  h4 : 192.168.10.22")
    print("h5 : 192.168.10.31  |  h6 : 192.168.10.32")
    print("h7 : 192.168.10.41  |  h8 : 192.168.10.42")
    print("==========================================\n")

    CLI(net)

    print("*** Stopping Network")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    build()
