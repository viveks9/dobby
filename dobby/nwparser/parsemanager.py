#!/usr/bin/env python3
"""Base class for parsing summaries generated by click.
"""
import json
from collections import deque

import dobby.nwinfo.networksummary as networksummary
import dobby.nwparser.parsewirelesssummary as parsewirelesssummary
import dobby.nwparser.parsetcpmystery as parsetcpmystery
import dobby.nwparser.parsetcploss as parsetcploss
import dobby.nwparser.parsenodesummary as parsenodesummary
import dobby.utils.util as util

__author__ = """\n""".join(['Vivek Shrivastava (vivek@obiai.tech)'])

class ParseManager(object):
    """Parsing manager which coordinates all the parsing
    """
    def __init__(self, max_summaries=None):
        self.summary_queue = deque([], None)
        self.wireless_parser = parsewirelesssummary.ParseWirelessSummary()
        self.tcpmystery_parser = parsetcpmystery.ParseTCPMysterySummary()
        self.tcploss_parser = parsetcploss.ParseTCPLossSummary()
        self.nodesummary_parser = parsenodesummary.ParseNodeSummary()

    def find_summary(self, timestamp):
        for summary in list(reversed(self.summary_queue)):
            #TODO -- handle summary.start_ts/end_ts being none
            if timestamp >= summary.start_ts and timestamp < summary.end_ts:
                return summary
        return None


    def parse_summary(self, start_ts=None, end_ts=None,
                      wireless_stream=None, node_stream=None,
                      tcploss_stream=None, tcpmystery_stream=None):
        ns = networksummary.NetworkSummary()
        ns.start_ts = start_ts
        ns.end_ts = end_ts
        #Parse wireless
        if wireless_stream:
            wireless_json = util.read_json(wireless_stream)
            ns = self.wireless_parser.parse_summary(wireless_json=wireless_json,
                                                    network_summary=ns)

        #Parse Node summary
        if node_stream:
            node_json = util.read_json(node_stream)
            ns = self.nodesummary_parser.parse_summary(node_json=node_json,
                                                       network_summary=ns)

        #Parse TCP Mystery
        if tcpmystery_stream:
            tcpmystery_json = util.read_json(tcpmystery_stream)
            ns = self.tcpmystery_parser.parse_summary(tcpmystery_json=tcpmystery_json,
                                                      network_summary=ns)

        #Parse TCP Loss
        if tcploss_stream:
            tcploss_json = util.read_json(tcploss_stream)
            ns = self.tcploss_parser.parse_summary(tcploss_json=tcploss_json,
                                                   network_summary=ns)

        self.summary_queue.append(ns)
        return ns

def main():
    parse_manager = ParseManager()

if __name__ == '__main__':
    main()
