from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

class LoopTopo(Topo):
    def build(self):
        # Add hosts
        h1 = self.addHost('h1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03')

        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Connect hosts to switches
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)

        # Connect switches to form a loop (Triangle)
        self.addLink(s1, s2)
        self.addLink(s2, s3)
        self.addLink(s3, s1)

if __name__ == '__main__':
    setLogLevel('info')
    
    # Initialize the custom topology
    topo = LoopTopo()
    
    # Create the network, pointing to your local Pox controller
    net = Mininet(topo=topo, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633))    
    net.start()
    print("*** Network Started. Type 'pingall' to test, or 'exit' to quit.")
    CLI(net)
    net.stop()