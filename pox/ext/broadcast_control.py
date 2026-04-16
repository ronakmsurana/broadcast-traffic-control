from pox.core import core
import pox.openflow.libopenflow_01 as of
import logging
logging.getLogger("packet").setLevel(logging.CRITICAL)

log = core.getLogger()


class BroadcastMitigator(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        self.broadcast_count = 0
        self.THRESHOLD = 15  # Limit before we start dropping
        # MAC to Port mapping for this switch
        self.macToPort = {}

    def _handle_PacketIn(self, event):
        packet = event.parsed
        
        # Learn the source MAC port mapping safely (prevents flapping in physical loops)
        if packet.src not in self.macToPort:
            self.macToPort[packet.src] = event.port

        # 1. Detect Broadcast Packets (ff:ff:ff:ff:ff:ff)
        if packet.dst.is_broadcast:
            self.broadcast_count += 1
            
            if self.broadcast_count > self.THRESHOLD:
                log.warning(f"Storm Detected at switch {event.dpid}! Count: {self.broadcast_count}. Dopping packets. ")
                
                # Install a flow rule to drop broadcast packets at the hardware layer
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match(dl_dst=packet.dst) # Match broadcast MAC
                msg.idle_timeout = 10  # Short timeout lets legitimate ARPs work after storm clears
                msg.hard_timeout = 20
                msg.priority = 100     # Higher priority than default rules
                # No actions appended = drop the packet
                msg.flags = of.OFPFF_SEND_FLOW_REM
                self.broadcast_count = 0
                self.connection.send(msg)
                return
            else:
                log.info(f"Broadcast allowed. from swicth {event.dpid} Count: {self.broadcast_count}")
                
        # Prevent IPv6/Multicast storms that lock up Mininet invisibly
        elif packet.dst.is_multicast:
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match(dl_dst=packet.dst)
            msg.hard_timeout = 60
            self.connection.send(msg)
            return

        # 2. Normal Forwarding (MAC Learning)
        if packet.dst in self.macToPort:
            # We know the port, install a flow rule for forwarding unicast traffic
            port = self.macToPort[packet.dst]
            
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match(dl_dst=packet.dst)
            msg.actions.append(of.ofp_action_output(port=port))
            # Optional timeouts for unicast
            msg.idle_timeout = 60
            msg.hard_timeout = 120
            self.connection.send(msg)
            
            # Forward the current packet out of the learned port
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=port))
            msg.data = event.ofp
            msg.in_port = event.port
            self.connection.send(msg)
        else:
            # We don't know the port yet, flood it
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
            msg.data = event.ofp
            msg.in_port = event.port
            self.connection.send(msg)
    def _handle_FlowRemoved(self, event):
        """
        This function is automatically triggered when the switch 
        deletes a rule that had the OFPFF_SEND_FLOW_REM flag set.
        """
        # Check if the rule removed was our broadcast block rule
        if event.ofp.match.dl_dst == of.EthAddr("ff:ff:ff:ff:ff:ff"):
            
            # Figure out exactly why the switch deleted it
            if event.ofp.reason == of.OFPRR_IDLE_TIMEOUT:
                reason = "Idle Timeout (10s of no broadcasts)"
            elif event.ofp.reason == of.OFPRR_HARD_TIMEOUT:
                reason = "Hard Timeout (20s maximum reached)"
            else:
                reason = "Manual Deletion"
                
            # Print the alert to your terminal
            log.info(f"🟢 LOCKDOWN LIFTED: Switch {event.dpid} is open. Reason: {reason}")
def launch():
    """Starts the component"""
    def start_switch(event):
        log.debug(f"Controlling switch {event.connection.dpid}")
        BroadcastMitigator(event.connection)
    
    core.openflow.addListenerByName("ConnectionUp", start_switch)
