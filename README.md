# SDN Broadcast Storm Control

## Overview
This project implements a reactive Software-Defined Networking (SDN) controller 
using POX to detect and mitigate broadcast storms in looped network topologies.

## Features
* Sliding Window Rate Limiting: Detects storms based on packet velocity (15 packets / 5 seconds).
* Isolated State Management: Tracks broadcast thresholds independently per switch.
* Hardware-Level Mitigation: Installs high-priority drop rules directly to the switch data plane.
* Auto-Recovery: Utilizes OpenFlow hard timeouts to lift network lockdowns automatically.
* Topology Support: Includes custom Mininet scripts for 3-switch (triangle) and 4-switch (square) loops.

## Requirements
* Mininet
* POX Controller
* Python 3

## File Structure
* `broadcast_control.py`: The POX controller application containing the sliding window and OpenFlow logic.
* `topo.py`: Mininet script generating a 3-switch triangle loop topology.
* `topo2.py`: Mininet script generating a 4-switch square loop topology.

## Execution
1. Start the POX controller:
   ```bash
   cd pox
   python3 pox.py broadcast_contro
   ```
2. Start the Mininet topology (in a separate terminal):
   ```bash
   sudo python3 topo.py
   ```
3. Trigger network discovery and observe mitigation:
   ```bash
   mininet> pingall
   ```
4. Test targeted flood attack (from Mininet CLI):
   ```bash
   mininet> h1 ping -f -b 10.255.255.255
   ```

## Expected Behavior
The controller will allow initial ARP broadcasts for host discovery. Once the physical loop 
duplicates the broadcast beyond the threshold, the controller pushes an `OFPFF_SEND_FLOW_REM` 
flagged drop rule to the overloaded switch. After 30 seconds, the lockdown is lifted and 
standard traffic resumes.