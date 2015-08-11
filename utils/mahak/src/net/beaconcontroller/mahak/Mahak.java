/*    
    <Mahak -- Beacon Controller to load STanford backbone network into Mininet.
    
    @Author Peyman Kazemian
    @Author James Hongyi Zeng
*/

package net.beaconcontroller.mahak;

import org.openflow.protocol.*;
import org.openflow.protocol.action.*;
import org.openflow.util.U16;
import net.beaconcontroller.core.*;

import java.io.*;
import java.util.ArrayList;

import org.codehaus.jackson.*;
import org.codehaus.jackson.map.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class Mahak implements IOFMessageListener, IOFSwitchListener {
    private final int NX_VENDOR_ID = 0x00002320;
    protected IBeaconProvider beaconProvider;
    protected static Logger log = LoggerFactory.getLogger(Mahak.class);
    protected String[] switchNames = {"bbra_rtr",
            "bbrb_rtr",
            "boza_rtr",
            "bozb_rtr",
            "coza_rtr",
            "cozb_rtr",
            "goza_rtr",
            "gozb_rtr",
            "poza_rtr",
            "pozb_rtr",
            "roza_rtr",
            "rozb_rtr",
            "soza_rtr",
            "sozb_rtr",
            "yoza_rtr",
            "yozb_rtr"};
    
    public IBeaconProvider getBeaconProvider() {
        return beaconProvider;
    }
 
    public void setBeaconProvider(IBeaconProvider beaconProvider) {
        this.beaconProvider = beaconProvider;
    }
    
    public void startUp() {
        beaconProvider.addOFMessageListener(OFType.PACKET_IN, this);
        beaconProvider.addOFSwitchListener(this);
    }
 
    public void shutDown() {
        beaconProvider.removeOFMessageListener(OFType.PACKET_IN, this);
        beaconProvider.removeOFSwitchListener(this);
    }
    
    public Command receive(IOFSwitch sw, OFMessage msg) {
        return Command.CONTINUE;
    }

    public String getName() {
        return "Mahak";
    }
    
    private short transformPort(int port) {
        short result = (short) ((port % 10000) + 1000 * ((port % 100000) / 10000));
        // James : avoid port 0
        if (result == (short) 0){
            result = (short) 1000;
        }
        return result;
    }
    
    private boolean isIntermediatePort(short port) {
        if (port / 1000 == 1 || port == (short) 1000) return true;
        else return false;
    }
    
    private ArrayList<OFMatch> makeOFMatch(JsonNode ruleNode) {
        ArrayList<OFMatch> matches = new ArrayList<OFMatch>();
        OFMatch match = new OFMatch();
        int wildcard = OFMatch.OFPFW_ALL;
        if (ruleNode.get("vlan_match") != null) {
            if (ruleNode.get("vlan_wc").getIntValue() == 0 & ruleNode.get("vlan_match").getIntValue() != 0) {
                System.out.println("has vlan");
                match.setDataLayerVirtualLan((short)ruleNode.get("vlan_match").getIntValue());
                wildcard = wildcard & ~(OFMatch.OFPFW_DL_VLAN);
            }
        }
        if (ruleNode.has("ip_proto_match")) {
            if (ruleNode.get("ip_proto_wc").getIntValue() == 0) {
                match.setNetworkProtocol((byte)ruleNode.get("ip_proto_match").getIntValue());
                wildcard = wildcard & ~(OFMatch.OFPFW_NW_PROTO);
            }
        }
        if (ruleNode.has("transport_src_match")){
            if (ruleNode.get("transport_src_wc").getIntValue() == 0) {
                match.setTransportSource((short)ruleNode.get("transport_src_match").getIntValue());
                wildcard = wildcard & ~(OFMatch.OFPFW_TP_SRC);
            }
        }
        if (ruleNode.has("transport_dst_match")) {
            if (ruleNode.get("transport_dst_wc").getIntValue() == 0) {
                match.setTransportDestination((short)ruleNode.get("transport_dst_match").getIntValue());
                wildcard = wildcard & ~(OFMatch.OFPFW_TP_DST);
            }
        }
        // Ethernet protocol = IP (0x0800)
        match.setDataLayerType((short)0x0800);
        wildcard = wildcard & ~(OFMatch.OFPFW_DL_TYPE);
        
        // IP SRC
        if (ruleNode.has("ip_src_match")) {
            match.setNetworkSource(ruleNode.get("ip_src_match").getIntValue());
            int maskLen = ruleNode.get("ip_src_wc").getIntValue();
            wildcard = (wildcard & ~(OFMatch.OFPFW_NW_DST_MASK)) | (maskLen << OFMatch.OFPFW_NW_DST_SHIFT);
        }
        // IP DST
        if (ruleNode.has("ip_dst_match")) {
            match.setNetworkDestination(ruleNode.get("ip_dst_match").getIntValue());
            int maskLen = ruleNode.get("ip_dst_wc").getIntValue();
            wildcard = (wildcard & ~(OFMatch.OFPFW_NW_DST_MASK)) | (maskLen << OFMatch.OFPFW_NW_DST_SHIFT);
        }
        
        // IN PORT
        /* HACK! match on all in_ports. wildcard in_port field.
         * FIX ME!
         * *
        wildcard = wildcard & ~(OFMatch.OFPFW_IN_PORT);
        match.setWildcards(wildcard);
        for (int i=0; i < ruleNode.get("in_ports").size(); i++) {
            OFMatch matchCopy = match.clone();
            short inPort = this.transformPort(ruleNode.get("in_ports").get(i).getIntValue());
            System.out.println("Match Port :" + inPort);
            matchCopy.setInputPort(inPort);
            matches.add(matchCopy);
        }
        */
        match.setWildcards(wildcard);
        matches.add(match);
        
        return matches;
    }
    
    private ArrayList<OFAction> makeOFAction(JsonNode ruleNode) {
        ArrayList<OFAction> result = new ArrayList<OFAction>();
        if (ruleNode.has("vlan_wc")) {
            if (ruleNode.get("vlan_new")!=null && !ruleNode.get("vlan_new").isNull()) {
                if (ruleNode.get("vlan_new").getIntValue() == 0) {
                    OFActionStripVirtualLan action = new OFActionStripVirtualLan();
                    result.add(action);
                } else {
                    short newVlan = (short)ruleNode.get("vlan_new").getIntValue();
                    OFActionVirtualLanIdentifier action = new OFActionVirtualLanIdentifier();
                    action.setVirtualLanIdentifier(newVlan);
                    result.add(action);
                }
            }
        }
        if (ruleNode.has("ip_src_new")) {
            if ( ruleNode.get("ip_src_new")!=null && !ruleNode.get("ip_src_new").isNull()) {
                OFActionNetworkLayerSource action = new OFActionNetworkLayerSource();
                action.setNetworkAddress(ruleNode.get("ip_src_new").getIntValue());
                result.add(action);
            }
        }
        if (ruleNode.has("ip_dst_new")) {
            if (ruleNode.get("ip_dst_new")!=null && !ruleNode.get("ip_dst_new").isNull()) {
                OFActionNetworkLayerSource action = new OFActionNetworkLayerSource();
                action.setNetworkAddress(ruleNode.get("ip_dst_new").getIntValue());
                result.add(action);
            }
        }
        if (ruleNode.has("transport_src_new")) {
            if (ruleNode.get("transport_src_new")!=null && !ruleNode.get("transport_src_new").isNull()) {
                OFActionTransportLayerSource action = new OFActionTransportLayerSource();
                action.setTransportPort((short)ruleNode.get("transport_src_new").getIntValue());
                result.add(action);
            }
        }
        if (ruleNode.has("transport_dst_new")) {
            if (ruleNode.get("transport_dst_new")!=null && !ruleNode.get("transport_dst_new").isNull()) {
                OFActionTransportLayerDestination action = new OFActionTransportLayerDestination();
                action.setTransportPort((short)ruleNode.get("transport_dst_new").getIntValue());
                result.add(action);
            }
        }
        for (int i = 0; i < ruleNode.get("out_ports").size(); i++) {
            short outPort = this.transformPort(ruleNode.get("out_ports").get(i).getIntValue());
            if (this.isIntermediatePort(outPort)) {
                OFActionVendor action = new OFActionVendor();
                // set up fields
                action.setVendor(this.NX_VENDOR_ID);
                action.setLength((short) 16);
                byte [] content = new byte[8];
                content[0] = (byte) 0;
                content[1] = (byte) 1;
                content [2] = (byte)(outPort/256);
                content [3] = (byte)(outPort%256); 
                action.setContent(content);
                // add to the list of actions
                result.add(action);
            } else {
                // James: use physical port..
                OFAction action = new OFActionOutput()
                .setPort((short) (outPort % 1000));
                result.add(action);
            }
        }
        if (result.size() == 0) {
            //result.add(new OFActionOutput());
        }
        return result;
    }
    
    private short actionsLength(ArrayList<OFAction> actions) {
        short result = 0;
        for (int i =0; i < actions.size(); i++) {
            result += actions.get(i).getLength();
        }
        return result;
    }
    
    @SuppressWarnings("deprecation")
    public void addedSwitch(IOFSwitch sw) {

        int switchIndex = (int) ((sw.getId()) - 1);
        if (switchIndex > this.switchNames.length)
            return;
        
        String switchName = this.switchNames[switchIndex];
        System.out.println("SWITCH JOINED: " + switchName);
        try{
            ObjectMapper m = new ObjectMapper();            
            JsonNode rootNode = m.readValue(new File("/tmp/of_rules/"+switchName+".of"), JsonNode.class);
            JsonNode rulesNode = rootNode.path("rules");
            short priority = 0;
            for (int i=0; i<rulesNode.size(); i++) {
                JsonNode ruleNode = rulesNode.get(i);
                ArrayList<OFMatch> matches = this.makeOFMatch(ruleNode);
                ArrayList<OFAction> actions = this.makeOFAction(ruleNode);
                System.out.println("---------------------");
                System.out.println("Matches: " + matches);
                System.out.println("Actions: " + actions);
                for (int j = 0; j < matches.size(); j++) {
                    OFFlowMod fm = new OFFlowMod();
                    fm.setBufferId(-1)
                    .setCommand(OFFlowMod.OFPFC_ADD)
                    .setIdleTimeout((short) 0)
                    .setMatch(matches.get(j))
                    .setActions(actions)
                    .setPriority((short)(60000-priority))
                    .setLengthU(U16.t(OFFlowMod.MINIMUM_LENGTH+this.actionsLength(actions)));
                    try {
                        System.out.println("Flow Mod: " + fm.toString());
                        sw.getOutputStream().write(fm);
                    } catch (IOException e) {
                        log.error("Failure writing FlowMod", e);
                    }
                    priority += 1;
                }
                System.out.println("---------------------");
            }
        } catch (Exception e) {
            System.out.print(e);
        }
    }

    public void removedSwitch(IOFSwitch sw) {
        
    }

}
