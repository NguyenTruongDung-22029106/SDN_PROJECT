#!/usr/bin/python
"""
SDN Topology with IoT-like devices
Enhanced topology for ML + Blockchain testing
"""
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.link import TCLink
from time import sleep
import random
import os

'''
Network Topology:

                    s1 (Main Switch)
                     |
    +----------------+----------------+
    |                |                |
   s2               s3               s4
    |                |                |
  h1-h4           h5-h8            h9-h12

Total: 12 hosts, 4 switches
Simulates multi-domain SDN with potential attack sources
'''

TEST_TIME = int(os.getenv('TEST_TIME', '300'))  # seconds the traffic generator should run
# Modes: manual | normal | attack
TEST_TYPE = os.getenv('TEST_TYPE', 'manual')
# No default TARGET_IP required for manual mode; scripts handle empty target themselves
TARGET_IP = ''

class MultiSwitchTopo(Topo):
    """Multi-switch topology for advanced testing"""
    
    def build(self):
        # Create switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        
        # Link switches
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s1, s4, cls=TCLink, bw=10)
        
        # Add hosts to s2 (normal IoT devices) - Using same subnet for routing
        for i in range(1, 5):
            h = self.addHost(f'h{i}', 
                           ip=f'10.0.0.{i}/24',
                           mac=f"00:00:00:00:01:{i:02d}")
            self.addLink(h, s2, cls=TCLink, bw=5)
        
        # Add hosts to s3 (mixed devices) - Using same subnet for routing
        for i in range(5, 9):
            h = self.addHost(f'h{i}',
                           ip=f'10.0.0.{i}/24',
                           mac=f"00:00:00:00:02:{(i-4):02d}")
            self.addLink(h, s3, cls=TCLink, bw=5)
        
        # Add hosts to s4 (potential attackers) - Using same subnet for routing
        for i in range(9, 13):
            h = self.addHost(f'h{i}',
                           ip=f'10.0.0.{i}/24',
                           mac=f"00:00:00:00:03:{(i-8):02d}")
            self.addLink(h, s4, cls=TCLink, bw=5)


class SingleSwitchTopo(Topo):
    """Single switch connected to 10 hosts (original topology)"""
    
    def build(self):
        s1 = self.addSwitch('s1')
        
        for i in range(1, 11):
            h = self.addHost(f'h{i}',
                           ip=f'10.1.1.{i}/24',
                           mac=f"00:00:00:00:00:{i:02d}",
                           defaultRoute="via 10.1.1.10")
            self.addLink(h, s1, cls=TCLink, bw=5)


def run_normal_traffic(net):
    """Generate normal traffic pattern"""
    print("Generating NORMAL Traffic...")
    
    hosts = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9', 'h10']
    
    for hostname in hosts:
        h = net.get(hostname)
        cmd = "bash ../scripts/normal_traffic.sh &"
        h.cmd(cmd)
    
    sleep(TEST_TIME)


def run_attack_traffic(net):
    """Generate attack traffic pattern"""
    print("Generating ATTACK Traffic...")
    
    # Attacker hosts
    attackers = ['h1', 'h2']
    
    for hostname in attackers:
        h = net.get(hostname)
        cmd = "bash ../scripts/attack_traffic.sh &"
        h.cmd(cmd)
    
    sleep(TEST_TIME)


if __name__ == '__main__':
    setLogLevel('info')
    
    # Choose topology
    topo = MultiSwitchTopo()  # Multi-switch topology (4 switches: s1, s2, s3, s4)
    # topo = SingleSwitchTopo()  # Single switch topology (1 switch: s1)
    
    # Create network with remote controller
    c1 = RemoteController('c1', ip='127.0.0.1', port=6633)
    net = Mininet(topo=topo, controller=c1, switch=OVSSwitch)
    net.start()
    
    print("=" * 60)
    print("SDN Network Started")
    if isinstance(topo, MultiSwitchTopo):
        print("Topology: Multi-Switch (4 switches: s1, s2, s3, s4 with 12 hosts)")
    else:
        print("Topology: Single Switch with 10 Hosts")
    print("Controller: Ryu (127.0.0.1:6633)")
    print("=" * 60)
    
    if TEST_TYPE == "normal":
        run_normal_traffic(net)
        net.stop()
    
    elif TEST_TYPE == "attack":
        run_attack_traffic(net)
        net.stop()
    
    else:  # manual
        print("\nManual mode - use Mininet CLI")
        print("Examples:")
        print("  mininet> h1 ping h2")
        print("  mininet> h1 bash ../scripts/attack_traffic.sh &")
        print("  mininet> xterm h1")
        print("")
        CLI(net)
        net.stop()
