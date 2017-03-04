Create nodes for IPs if needed"""Base class for parsing summaries generated by click.
"""
from __future__ import division
from copy import deepcopy
from collections import Counter, defaultdict
from enum import Enum, unique
from classes.endpoint import EndPoint
from classes.edge import EdgeType, Edge
from classes.node import NodeType, Node
from classes.flow import Flow
from classes.app import NetworkApp
from classes.phymodel import PhysicalAddress, PhyModel, WifiPhysicalModel
from classes.metrics import Stats, Metrics, WirelessMetrics
import json

__author__ = """\n""".join(['Vivek Shrivastava (vivek@obiai.tech)'])

# Keyed by MAC
MAC_TO_ENDPOINTS = {}
# Keyed by IP
IP_TO_ENDPOINTS = {}
# Keyed by node uuid
NODES = {}
# Keyed by endpoint macs
EDGES = {}
# Keyed by flow ip:port->ip:port
IP_FLOWS = {}
# Keyed by the BSSID + Channel --> a given AP on a given channel
PHYMODELS = {}
# Keyed by app uuid
APPS = {}

# Assuming we represent values as 10/50/90 percentile
def convert_to_stats(value_string):
    vals = value_string.split('/')
    stats = Stats(pecentile_10=vals[0],
                  percentile_50=vals[1],
                  percentile_90=vals[2])


class ParseWirelessSummary(object):
    """Parses wireless summary generated by click
    """
    def __init__(self, fname=None)
        # Read in the summary
        with open(opts.json_file) as f:
            wireless_json = json.load(f)

        #Iterate and update the endpoint stats
        for link in wireless_json['links']['link']:
            ap = link['@ap']
            client = link['@client']
            bssid = link['@bssid']
            #TODO -- flow the channel information click
            channel = link['@channel']
            #TODO -- flow the SSID information from click

            #Create physical addresses
            ap_addr = PhysicalAddress(ap)
            client_addr = PhysicalAddress(client)
            bssid_addr = PhysicalAddress(bssid)

            # Create a phyModel for bssid
            wifi_model = PHYMODELS.get((bssid_addr, channel) , None)
            if wifi_model is None:
                # Create wifi model
                wifi_model = WifiPhysicalModel(mac=bssid_addr, channel=channel)
            else:
                wifi_model.add_clients(clients=[client_addr])

            # Create an endpoint entry for ap/client
            ap_endpoint = MAC_TO_ENDPOINTS.get(ap_addr, None)
            if not ap_endpoint:
                ap_endpoint = EndPoint(phy_address=ap_addr,
                                       phy_model=wifi_model)
                #TODO: It should be one AP node per ssid -- right now it is one AP node per mac
                #Create a new node for the AP
                ap_node = Node(endpoints=[ap_endpoint], node_type=NodeType.WIRELESS_ROUTER)
                ap_endpoint.node_id = ap_node.node_id
                MAC_TO_ENDPOINTS[ap_addr] = ap_endpoint
                NODES[ap_node.node_id] = ap_node

            client_endpoint = MAC_TO_ENDPOINTS.get(client_addr, None)
            if not client_endpoint:
                client_endpoint = EndPoint(phy_address=client_addr,
                                           phy_model=wifi_model)
                client_node = Node(endpoints=[client_endpoint], node_type=NodeType.WIRELESS_CLIENT)
                client_endpoint.node_id = client_node.node_id
                MAC_TO_ENDPOINTS[client_addr] = client_endpoint
                NODES[client_node.node_id] = client_node

            # Create an edge for this
            edge = EDGES.get((ap_addr, client_addr), None)
            if not edge:
                edge = Edge(endpoint_a=ap_addr, endpoint_b=client_addr, edge_type=EdgeType.PHYSICAL)

            for stream in link['stream']:
                start_ts = stream['@start_ts']
                end_ts = stream['@start_ts']
                total_data_bytes = stream['@total_data_bytes']
                total_data_pkts = stream['@total_data_pkts']
                total_pkts = stream['@total_pkts']
                total_retx = stream['@total_retx']
                total_trans_time_usec = stream['@total_trans_time_usec']
                rate_stats = convert_to_stats(stream['@rate'])
                size_stats = convert_to_stats(stream['@size'])
                snr_stats = convert_to_stats(stream['@snr'])
                metrics_to_add = WirelessMetrics(start_ts=start_ts, end_ts=end_ts,
                                                 total_pkts=total_pkts, total_bytes=total_bytes,
                                                 total_data_pkts=total_data_pkts,
                                                 total_data_bytes=total_data_bytes,
                                                 total_retx=total_retx, snr_stats=snr_stats,
                                                 rate_stats=rate_stats, size_stats=size_stats)
                if stream['@dir'] == "TODS":
                    #AP - a, client - b, this metric is for b->a
                    edge.update_metrics_ba(metrics_to_add)
                if stream['@dir'] == "FROMDS":
                    #AP - a, client - b, this metric is for a->b
                    edge.update_metrics_ab(metrics_to_add)
                if stream['@dir'] == "NODS":
                    #TODO -- fix this
                    #Not clear which is a and b here
                    edge.update_undirected_metrics(metrics_to_add)
                if stream['@dir'] == "DSTODS":
                    #TODO -- fix this
                    #Not clear which is a and b here
                    edge.update_undirected_metrics(metrics_to_add)

            #Inserting the physical model into the global dict
            PHYMODELS[(bssid_addr, channel)] = wifi_model
            #Inserting the edge into the global edges table
            EDGES[(ap_addr, client_addr)] = edge
            #TODO -- update the interferers by checking for other bssids on the same channel
            #TODO -- Add nodes for physical endpoints and ips


class ParseNodeSummary(object):
    """Parses wireless summary generated by click
    """
    def __init__(self, json_file=None)
        # Read in the summary
        with open(opts.json_file) as f:
            node_json = json.load(f)

        #Iterate and update the endpoint stats
        for node in node_json['nodes']['node']:
            mac = node['@ether']
            vendor = node['@vendor']
            phy_addr = PhysicalAddress(phy_address=mac, vendor=vendor)
            # See if this endpoint exists
            endpoint = MAC_TO_ENDPOINTS.get(phy_addr, None)
            if endpoint:
                #Endpoint exists. Just update the vendor
                endpoint.phy_address.update_vendor(vendor)
            else:
                endpoint = EndPoint(phy_addr)
                MAC_TO_ENDPOINTS[phy_addr] = endpoint
            # Check if a corresponding node exists
            if endpoint.node_id:
                node = NODES.get(endpoint.node_id, None)
                assert(node)
            else:
                # Create a node
                node = Node(endpoints=[endpoint], node_type=NodeType.UNKNOWN)
                endpoint.node_id = node.node_id
                NODES[node.node_id] = node

            for ip in node['ip']:
                # For each IP address, create an IPInfo element and create a node.
                ip_info = IPInfo(ipv4address=ip['addr'], hostname=ip.get('hostname', None))
                if node.node_type == NodeType.WIRELESS_ROUTER:
                    # Create an endpoint with ip_info -- assign it to the endpoint above if not AP
                    # TODO remove this hack -- IP-->MAC should be derived from ARP requests
                    ip_endpoint = EndPoint(ip_info = ip_info)
                    ip_node = Node(endpoints=[ip_endpoint], node_type=NodeType.CLOUD_IP)
                    ip_endpoint.node_id = ip_node.node_id
                    IP_TO_ENDPOINTS[ip_info.ipv4address] = ip_endpoint
                    NODES[ip_node.node_id] = ip_node
                else:
                    # Add to the MAC endpoint above
                    endpoint.update_ip(ip_info=ip_info)
                    IP_TO_ENDPOINTS[ip_info.ipv4address] = endpoint

class ParseTCPSummary(object):
    """
    Base class for a Flow.

    Flow {
        Vector edgeList[MAX_HOPS] // An ordered list of edges
        FlowType flowType[MAX_PROTOCOL_LAYERS] // A list of protocols like HTTP/TCP/IP
        Int Port
        FlowMetrics flowMetrics  // Captures network metrics for this flow.
    }

    """
    def __init__(self, tcpmystery_file=None, tcploss_file=None)
        # Read in the summary
        if tcpmystery_file:
            with open(opts.tcpmystery_file) as f:
                self.tcpmystery_json = json.load(f)
        if tcploss_file:
            with open(opts.tcploss_file) as f:
                self.tcploss_json = json.load(f)

    def parse_tcp_summary(self):
        # First parse tcpmystery
        for flow in self.tcpmystery_json['@trace']['flow']:
            tcp_flow_info = {}
            src_ip = IPInfo(ipv4address=flow['@src'])
            src_ip_endpoint = IP_TO_ENDPOINTS.get(src_ip.ipv4address, None)
            if not src_ip_endpoint:
                src_ip_endpoint = EndPoint(ip_info=src_ip)
            if not src_ip_endpoint.node_id:
                src_ip_node = Node(endpoints=[src_ip_endpoint], node_type=NodeType.UNKNOWN)
                src_ip_endpoint.node_id = src_ip_node.node_id
                NODES[src_ip_node.node_id] = src_ip_node
            else:
                src_ip_node = NODES[src_ip_endpoint.node_id]
            IP_TO_ENDPOINTS[src_ip.ipv4address] = src_ip_endpoint
            tcp_flow_info['src_endpoint'] = src_ip_endpoint

            dst_ip = IPInfo(ipv4address=flow['@dst'])
            dst_ip_endpoint = IP_TO_ENDPOINTS.get(dst_ip.ipv4address, None)
            if not dst_ip_endpoint:
                dst_ip_endpoint = EndPoint(ip_info=dst_ip)
            if not dst_ip_endpoint.node_id:
                dst_ip_node = Node(endpoints=[src_ip_endpoint], node_type=NodeType.UNKNOWN)
                dst_ip_endpoint.node_id = dst_ip_node.node_id
                NODES[dst_ip_node.node_id] = dst_ip_node
            else:
                dst_ip_node = NODES[dst_ip_endpoint.node_id]
            IP_TO_ENDPOINTS[dst_ip.ipv4address] = dst_ip_endpoint
            tcp_flow_info['dst_endpoint'] = dst_ip_endpoint

            tcp_flow_info['sport'] = flow['@sport']
            tcp_flow_info['dport'] = flow['@dport']
            tcp_flow_info['duration'] = flow['@duration']
            flow_key = str(src_ip.ipv4address) + "-" + str(sport) + "-" +
                       str(dst_ip.ipv4address) + "-" + str(dport)

            # Generate the metrics for RTT/Semirtt/Loss
            for rtt in flow['rtt']:
                if rtt['@source'] == "min":
                    min_rtt = rtt['@value']
                elif rtt['@source'] == "avg":
                    avg_rtt = rtt['@value']
                elif rtt['@source'] == "max":
                    max_rtt = rtt['@value']
            rtt_stats = Stats(min_val=min_rtt, avg_val=avg_rtt, max_val=max_rtt)
            tcp_metrics = TCPMetrics(rtt_stats=rtt_stats, duration=duration)
            tcp_metrics_parameters = dict(rtt_stats=rtt_stats, duration=duration)
            tcp_flow_info['flow_metrics'] = tcp_metrics

            # Generate the metrics for each direction
            for stream in flow['stream']:
                mtu = stream['@mtu']
                nack = stream['@nack']
                data = stream['@ndata']
                nbytes = stream['@seqlen']
                min_rtt = None
                max_rtt = None
                avg_rtt = None
                for rtt in stream['semirtt']:
                    if rtt['@source'] == "min":
                        min_rtt = rtt['@value']
                    elif rtt['@source'] == "avg":
                        avg_rtt = rtt['@value']
                    elif rtt['@source'] == "max":
                        max_rtt = rtt['@value']
                    elif rtt['@source'] == "var":
                        var_rtt = rtt['@value']
                rtt_stats = Stats(min_val=min_rtt, avg_val=avg_rtt,
                                  max_val=max_rtt, var_val=var_rtt)
                tcp_metrics_directional = TCPMetrics(rtt_stats=rtt_stats, mtu=mtu,
                                                     total_acks=nack, total_data_pkts=data,
                                                     total_bytes=nbytes)
                tcp_metrics_directional_parameters = dict(rtt_stats=rtt_stats, mtu=mtu,
                                                     total_acks=nack, total_data_pkts=data,
                                                     total_bytes=nbytes)
                if stream['@dir'] == 0:
                    tcp_flow_info['flow_metrics_src_to_dst'] = tcp_metrics_directional
                    tcp_metrics_directional_parameters_0 = tcp_metrics_directional_parameters
                else:
                    tcp_flow_info['flow_metrics_dst_to_src'] = tcp_metrics_directional
                    tcp_metrics_directional_parameters_1 = tcp_metrics_directional_parameters

            #Get the tcp flow and insert it into the FLOWS dict
            tcp_flow = FLOWS.get(flow_key, None)
            if not tcp_flow:
                tcp_flow = Flow(**tcp_flow_info)
                FLOWS[flow_key] = tcp_flow
            else:
                tcp_flow.flow_metrics.update_stats(tcp_metrics_parameters)
                tcp_flow.flow_metrics_src_to_dst.update_stats(tcp_metrics_directional_parameters_0)
                tcp_flow.flow_metrics_dst_to_src.update_stats(tcp_metrics_directional_parameters_1)


    def parse_tcploss_json(self):
        # Parse tcploss.json
        for flow in self.tcploss_json['@trace']['flow']:
            tcp_flow_info = {}
            src_ip = IPInfo(ipv4address=flow['@src'])
            src_ip_endpoint = IP_TO_ENDPOINTS.get(src_ip.ipv4address, None)
            if not src_ip_endpoint:
                src_ip_endpoint = EndPoint(ip_info=src_ip)
            if not src_ip_endpoint.node_id:
                src_ip_node = Node(endpoints=[src_ip_endpoint], node_type=NodeType.UNKNOWN)
                src_ip_endpoint.node_id = src_ip_node.node_id
                NODES[src_ip_node.node_id] = src_ip_node
            else:
                src_ip_node = NODES[src_ip_endpoint.node_id]
            IP_TO_ENDPOINTS[src_ip.ipv4address] = src_ip_endpoint
            tcp_flow_info['src_endpoint'] = src_ip_endpoint

            dst_ip = IPInfo(ipv4address=flow['@dst'])
            dst_ip_endpoint = IP_TO_ENDPOINTS.get(dst_ip.ipv4address, None)
            if not dst_ip_endpoint:
                dst_ip_endpoint = EndPoint(ip_info=dst_ip)
            if not dst_ip_endpoint.node_id:
                dst_ip_node = Node(endpoints=[src_ip_endpoint], node_type=NodeType.UNKNOWN)
                dst_ip_endpoint.node_id = dst_ip_node.node_id
                NODES[dst_ip_node.node_id] = dst_ip_node
            else:
                dst_ip_node = NODES[dst_ip_endpoint.node_id]
            IP_TO_ENDPOINTS[dst_ip.ipv4address] = dst_ip_endpoint
            tcp_flow_info['dst_endpoint'] = dst_ip_endpoint

            tcp_flow_info['sport'] = flow['@sport']
            tcp_flow_info['dport'] = flow['@dport']
            flow_key = str(src_ip.ipv4address) + "-" + str(sport) + "-" +
                       str(dst_ip.ipv4address) + "-" + str(dport)


            # Generate the metrics for each direction
            total_losses_both_dir = 0
            total_losses_dir_0 = 0
            total_losses_dir_1 = 0
            for stream in flow['stream']:
                mtu = stream['@mtu']
                nack = stream['@nack']
                data = stream['@ndata']
                nbytes = stream['@seqlen']
                nfloss = stream['@nfloss']
                nloss = stream['@nloss']
                total_loss = nfloss + nloss
                total_losses_both_dir += total_loss
                if stream['@dir'] == 0:
                    total_losses_dir_0 = total_loss
                else:
                    total_losses_dir_1 = total_loss

            #Get the tcp flow and insert it into the FLOWS dict
            tcp_flow = FLOWS.get(flow_key, None)
            if not tcp_flow:
                tcp_metrics = TCPMetrics(total_loss=total_losses_both_dir)
                tcp_metrics_src_to_dst = TCPMetrics(total_loss=total_losses_dir_0)
                tcp_metrics_dst_to_src = TCPMetrics(total_loss=total_losses_dir_1)
                tcp_flow_info['flow_metrics'] = tcp_metrics
                tcp_flow_info['flow_metrics_src_to_dst'] = tcp_metrics_src_to_dst
                tcp_flow_info['flow_metrics_dst_to_src'] = tcp_metrics_dst_to_src
                tcp_flow = Flow(**tcp_flow_info)
                FLOWS[flow_key] = tcp_flow
            else:
                tcp_flow.flow_metrics.update_stats(dict(total_loss=total_losses_both_dir))
                tcp_flow.flow_metrics_src_to_dst.update_stats(dict(total_loss=total_losses_dir_0))
                tcp_flow.flow_metrics_dst_to_src.update_stats(dict(total_loss=total_losses_dir_1))


        #End of parsing TCP. Maybe print some stats.
