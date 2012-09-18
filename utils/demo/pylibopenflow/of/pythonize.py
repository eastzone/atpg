"""This module generate Python code for OpenFlow structs.

(C) Copyright Stanford University
Date December 2009
Created by ykk
"""
import pylibopenflow.cpythonize as cpythonize
from pylibopenflow.config import *

class rules(cpythonize.rules):
    """Class that specify rules for pythonization of OpenFlow messages

    (C) Copyright Stanford University
    Date December 2009
    Created by ykk
    """
    def __init__(self, ofmsg):
        """Initialize rules
        """
        cpythonize.rules.__init__(self)
        ##Reference to ofmsg
        self.__ofmsg = ofmsg
        ##Default values for members
        self.default_values[('ofp_header',
                             'version')] = "OFP_VERSION"
        self.default_values[('ofp_switch_config',
                             'miss_send_len')] = 'OFP_DEFAULT_MISS_SEND_LEN'
        for x in ['ofp_flow_mod','ofp_flow_expired','ofp_flow_stats']:
            self.default_values[(x,
                                 'priority')] = 'OFP_DEFAULT_PRIORITY'
            
        self.default_values[('ofp_match',
                             'dl_vlan')] = "OFP_VLAN_NONE"

        self.default_values[('ofp_action_output',
                             'type')] = 'OFPAT_OUTPUT'
        self.default_values[('ofp_action_output',
                             'len')] = 'OFP_ACTION_OUTPUT_BYTES'
        self.default_values[('ofp_action_nw_addr',
                             'len')] = 'OFP_ACTION_NW_ADDR_BYTES'
        self.default_values[('ofp_action_dl_addr',
                             'len')] = 'OFP_ACTION_DL_ADDR_BYTES'
        self.default_values[('ofp_action_tp_port',
                             'len')] = 'OFP_ACTION_TP_PORT_BYTES'
        self.default_values[('ofp_action_vlan_vid',
                             'type')] = 'OFPAT_SET_VLAN_VID'
        self.default_values[('ofp_action_vlan_vid',
                             'len')] = 'OFP_ACTION_SET_VLAN_VID_BYTES'
        self.default_values[('ofp_action_vlan_pcp',
                             'type')] = 'OFPAT_SET_VLAN_PCP'
        self.default_values[('ofp_action_vlan_pcp',
                             'len')] = 'OFP_ACTION_SET_VLAN_PCP_BYTES'
        self.default_values[('ofp_action_vendor_header',
                             'type')] = 'OFPAT_VENDOR'
        self.default_values[('ofp_action_enqueue',
                             'type')] = 'OFPAT_ENQUEUE'
        self.default_values[('ofp_action_enqueue',
                             'len')] = 'OFP_ACTION_ENQUEUE_BYTES'

        #Default values for struct
        self.struct_default[('ofp_hello',
                             'header')] = ".type = OFPT_HELLO"
        self.struct_default[('ofp_error_msg',
                             'header')] = ".type = OFPT_ERROR"
        
        self.struct_default[('ofp_switch_features',
                             'header')] = ".type = OFPT_FEATURES_REPLY"

        self.struct_default[('ofp_packet_in',
                             'header')] = ".type = OFPT_PACKET_IN"
        self.struct_default[('ofp_flow_removed',
                             'header')] = ".type = OFPT_FLOW_REMOVED"
        self.struct_default[('ofp_port_status',
                             'header')] = ".type = OFPT_PORT_STATUS"

        self.struct_default[('ofp_packet_out',
                             'header')] = ".type = OFPT_PACKET_OUT"
        self.struct_default[('ofp_flow_mod',
                             'header')] = ".type = OFPT_FLOW_MOD"
        self.struct_default[('ofp_port_mod',
                             'header')] = ".type = OFPT_PORT_MOD"
        
        self.struct_default[('ofp_stats_request',
                             'header')] = ".type = OFPT_STATS_REQUEST"        
        self.struct_default[('ofp_stats_reply',
                             'header')] = ".type = OFPT_STATS_REPLY"
        self.struct_default[('ofp_vendor_header',
                             'header')] = ".type = OFPT_VENDOR"

        self.default_values[('ofp_packet_out',
                             'buffer_id')] = 0xffffffff
        self.default_values[('ofp_flow_mod',
                             'buffer_id')] = 0xffffffff

        ##Macros to exclude
        self.excluded_macros = ['OFP_ASSERT(EXPR)','OFP_ASSERT(_EXPR)','OFP_ASSERT',
                                'icmp_type','icmp_code','OFP_PACKED',
                                'OPENFLOW_OPENFLOW_H']
        ##Enforce mapping
        if GEN_ENUM_VALUES_LIST:
            self.enforced_maps['ofp_header'] = [ ('type','ofp_type_values') ]
        elif GEN_ENUM_DICTIONARY:
            self.enforced_maps['ofp_header'] = \
                [ ('type','ofp_type_map.keys()') ]
        
class pythonizer(cpythonize.pythonizer):
    """Class that pythonize C structures of OpenFlow messages

    (C) Copyright Stanford University
    Date December 2009
    Created by ykk
    """
    def __init__(self, ofmsg):
        """Initialize
        """
        ofrules =  rules(ofmsg)
        cpythonize.pythonizer.__init__(self, ofmsg, ofrules)
        ##Reference to OpenFlow message class
        self.__ofmsg = ofmsg
