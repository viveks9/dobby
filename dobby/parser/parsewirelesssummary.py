"""Base class for parsing summaries generated by click.
"""
from __future__ import division
import copy
import dobby.nwifo.networksummary as networksummary
import dobby.nwmodel.phymodel as phymodel
import dobby.nwmodel.endpoint as endpoint
import dobby.nwmodel.edge as edge
import dobby.nwmodel.node as node
import dobby.nwmodel.flow as flow
import dobby.nwmodel.ipinfo as ipinfo
import dobby.nwmetrics.metrics as metrics
import dobby.utils.util as util

__author__ = """\n""".join(['Vivek Shrivastava (vivek@obiai.tech)'])

class ParseWirelessSummary(object):
    """Parses wireless summary generated by click
    """
    def parse_summary(self, wireless_json, network_summary=None):
        # Create an empty summary if none was provided
        if not network_summary:
            network_summary = networksummary.NetworkSummary()
        else:
            network_summary = copy.copy(network_summary)

        #Iterate and update the endpoint stats
        for link in wireless_json['links']['link']:
            ap = link['@ap']
            client = link['@client']
            bssid = link['@bssid']
            #TODO -- flow the channel information click
            channel = link.get('@channel', 0)
            #TODO -- flow the SSID information from click

            #Create physical addresses
            ap_addr = phymodel.PhysicalAddress(ap)
            client_addr = phymodel.PhysicalAddress(client)
            bssid_addr = phymodel.PhysicalAddress(bssid)

            # Create a phyModel for bssid
            wifi_model = network_summary.phy_models.get((str(bssid_addr), channel) , None)
            if wifi_model is None:
                # Create wifi model
                wifi_model = phymodel.WifiPhysicalModel(mac=bssid_addr, channel=channel)
            else:
                wifi_model.add_clients(clients=[client_addr])

            # Create an endpoint entry for ap/client
            ap_endpoint = network_summary.mac_to_endpoints.get(str(ap_addr), None)
            if not ap_endpoint:
                ap_endpoint = endpoint.EndPoint(phy_address=ap_addr,
                                       phy_model=wifi_model)
                #TODO: It should be one AP node per ssid -- right now it is one AP node per mac
                #Create a new node for the AP
                ap_node = node.Node(endpoints=[ap_endpoint], node_type=node.NodeType.WIRELESS_ROUTER)
                ap_endpoint.node_id = ap_node.node_id
                network_summary.mac_to_endpoints[str(ap_addr)] = ap_endpoint
                network_summary.nodes[ap_node.node_id] = ap_node

            client_endpoint = network_summary.mac_to_endpoints.get(str(client_addr), None)
            if not client_endpoint:
                client_endpoint = endpoint.EndPoint(phy_address=client_addr,
                                           phy_model=wifi_model)
                client_node = node.Node(endpoints=[client_endpoint], node_type=node.NodeType.WIRELESS_CLIENT)
                client_endpoint.node_id = client_node.node_id
                network_summary.mac_to_endpoints[str(client_addr)] = client_endpoint
                network_summary.nodes[client_node.node_id] = client_node

            # Create an edge for this
            edge = network_summary.edges.get((str(ap_addr), str(client_addr)), None)
            if not edge:
                edge = edge.Edge(endpoint_a=ap_addr, endpoint_b=client_addr, edge_type=edge.EdgeType.PHYSICAL)

            if type(link['stream']) != list:
                stream_list = [link['stream']]
            else:
                stream_list = link['stream']
            for stream in stream_list:
                assert(type(stream) == dict)
                start_ts = stream.get('@start_ts', None)
                if start_ts:
                    start_ts = int(start_ts)
                end_ts = stream.get('@end_ts', None)
                if end_ts:
                    end_ts = int(end_ts)
                total_data_bytes = util.get_float_value(stream, '@total_data_bytes')
                total_data_pkts = util.get_float_value(stream, '@total_data_pkts')
                total_pkts = util.get_float_value(stream, '@total_pkts')
                total_retx = util.get_float_value(stream, '@total_retx')
                total_trans_time_usec = util.get_float_value(stream, '@total_trans_time_usec')
                avg_data_pkt_duration_usec = util.get_float_value(stream, '@avg_data_pkt_duration_usec')
                rate_stats = convert_to_stats(stream.get('@rate', None), total_pkts)
                size_stats = convert_to_stats(stream.get('@size', None), total_pkts)
                snr_stats = convert_to_stats(stream.get('@snr', None), total_pkts)
                metrics_to_add = metrics.WirelessMetrics(start_ts=start_ts, end_ts=end_ts,
                                                 total_pkts=total_pkts,
                                                 total_data_pkts=total_data_pkts,
                                                 total_data_bytes=total_data_bytes,
                                                 total_retx=total_retx, snr_stats=snr_stats,
                                                 rate_stats=rate_stats, size_stats=size_stats,
                                                 total_trans_time_usec=total_trans_time_usec,
                                                 avg_data_pkt_duration_usec=avg_data_pkt_duration_usec)
                #if stream['@dir'] == "TODS":
                #TODO--switch this back to TODS in click
                if stream['@dir'] == "CLIENT-AP":
                    #AP - a, client - b, this metric is for b->a
                    print ("TODS: Adding edge metrics for:", str(ap_addr), str(client_addr))
                    edge.update_metrics_ba(metrics_to_add)
                #if stream['@dir'] == "FROMDS":
                #TODO--switch this back to FROMDS in click
                if stream['@dir'] == "AP-CLIENT":
                    #AP - a, client - b, this metric is for a->b
                    print ("FROMDS: Adding edge metrics for:", str(ap_addr), str(client_addr))
                    edge.update_metrics_ab(metrics_to_add)
                if stream['@dir'] == "NODS":
                    #TODO -- fix this
                    #Not clear which is a and b here
                    edge.update_undirected_metrics(metrics_to_add)
                #if stream['@dir'] == "DSTODS":
                #TODO--switch this back to DSTODS in click
                if stream['@dir'] == "AP-AP":
                    #TODO -- fix this
                    #Not clear which is a and b here
                    edge.update_undirected_metrics(metrics_to_add)

            #Inserting the physical model into the global dict
            network_summary.phy_models[(str(bssid_addr), channel)] = wifi_model
            #Inserting the edge into the global edges table
            network_summary.edges[(str(ap_addr), str(client_addr))] = edge
            #TODO -- update the interferers by checking for other bssids on the same channel
            #TODO -- Add nodes for physical endpoints and ips

        return network_summary
