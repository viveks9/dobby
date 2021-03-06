#!/usr/bin/env python3
"""Utility class for a physical addresses and physical layer model.
PhyModel:  A data structure that captures a physical layer and the networking aspects of that layer.
"""
import re
import time
from collections import Counter
import enum

__author__ = """\n""".join(['Vivek Shrivastava (vivek@obiai.tech)'])


def check_mac(mac_to_check):
    if not mac_to_check:
        return False
    return re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_to_check.lower())

class PhysicalAddress(object):
    """
    Base class for Physical Address.

    PhysicalAddress : {
      UInt48 phy_address;
    }

    """

    def __init__(self, phy_address=None, vendor=None):
        """Initialize an address and its attributes.
        Parameters
        ----------
        phy_address : input Ethernet Address
        attr : keyword arguments, optional (default= no attributes)
          Attributes to add to graph as key=value pairs.
        """
        if not check_mac(phy_address):
          print('Incorrect format of input mac, should be (AA:BB:CC:DD:EE:FF). Input={0}'.format(phy_address))
          self.phy_address = None
        else:
            self.phy_address = phy_address.lower().replace("-",":")
        self.vendor = vendor
        #self.__dict__.update((k,v) for k,v in locals().iteritems() if k != 'self')

    def __hash__(self):
        return hash(self.phy_address)

    def __eq__(self, other):
        return (self.phy_address) == (other.phy_address)

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)

    def __str__(self):
        return self.phy_address

    def __repr__(self):
        return self.__str__()

    def update_vendor(self, vendor):
        self.vendor = vendor

    def __gt__(self, other):
        return self.phy_address > other.phy_address

@enum.unique
class PhysicalModelTypes(enum.Enum):
    UNKNOWN = 0
    ETHERNET = 1
    WIFI = 2
    BLUETOOTH_CLASSIC = 4
    BLE = 5
    ZIGBEE = 6
    INFRARED = 7
    DOCSIS = 8

#See https://en.wikipedia.org/wiki/Maximum_transmission_unit
class PhysicalLayerMTU(enum.Enum):
    UNKNOWN = 0
    ETHERNET = 1500
    WIFI = 2304

class PhysicalModel(object):
    """ Class representing the physical link between nodes
    PhyModel {
        PhyType phyType
        int mtu // MTU for the link
        union {
            WifiPhyModel wifiPhyModel
            EthPhyModel ethPhyModel
            Any other models ..
        }
    }
    """
    def __init__(self, phy_type=PhysicalModelTypes.UNKNOWN, mtu=PhysicalLayerMTU.UNKNOWN):
        self.phy_type = phy_type
        self.mtu = mtu

class WifiPhysicalModel(PhysicalModel):
    """
    Physical Model for WiFi

    WifiPhyModel {
      PhyAddress apMac
      String ssid
      Int channel
      Set<Endpoint> clients
      Set<Endpoint> interferers
      Metrics channelUtilization
      Metrics pktLoss
      .. any other metrics ..
    }
    """
    def __init__(self, mac, ssid=None, channel=0, clients=[], interferers=[], **kwargs):
        """Initialize a wireless model and its related attributes.
        Parameters
        ----------
        mac: AP's MAC Address
        attr : keyword arguments, optional (default= no attributes)
          Attributes to add to graph as key=value pairs.
        """
        PhysicalModel.__init__(self, phy_type=PhysicalModelTypes.WIFI, mtu=PhysicalLayerMTU.WIFI)
        self.clients = set()
        self.interferers = set()
        self.wifi_stats = Counter()
        self.ssid = ssid
        self.channel = channel
        self.last_seen = time.time()
        self.mac = mac
        self.clients.update(clients)
        self.interferers.update(interferers)
        self.__dict__.update(kwargs)

    def add_clients(self, clients):
        """Add to the list of clients.
        """
        self.clients.update(clients)

    def add_interferers(self, interferers):
        """Add to interferer list.
        """
        self.interferers.update(interferers)

    def update_last_seen(self):
        """Update last seen timestamp.
        """
        self.last_seen = time.time()

    def update_stats(self, **stats):
        """Update stats.
        """
        # Using counters here for most keys
        self.wifi_stats.update(stats)

