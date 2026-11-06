# NetSage AI - Broken Lab Troubleshooting Demo Script & Walkthrough

This document outlines the **5-to-10 minute presentation & live demo walkthrough** for **NetSage AI**, showing a broken Packet Tracer lab being diagnosed, reviewed by a human engineer, fixed on Cisco IOS, and verified end-to-end.

---

## ⏱️ Video Demo Timeline (Target: 6 - 8 Minutes)

| Time | Phase | Focus |
| :--- | :--- | :--- |
| **0:00 - 1:15** | **1. Problem Introduction** | Problem Statement, Junior Engineer challenges, NetSage AI architecture & Safety Gate. |
| **1:15 - 2:30** | **2. Lab Setup & Symptoms** | Loading broken Packet Tracer lab (`NET-010` - Cross-VLAN DHCP Relay Failure). |
| **2:30 - 3:45** | **3. AI Diagnosis & Rule Check** | Running Python Rule Checker + NetSage AI structured prompt with evidence quotation. |
| **3:45 - 5:15** | **4. Mandatory Human Review** | Human engineer triage (Accept / Edit / Reject), Responsible AI audit on flawed cases. |
| **5:15 - 6:30** | **5. Remediation & Fix** | Applying Cisco IOS configuration (`ip helper-address 192.168.50.2`). |
| **6:30 - 7:30** | **6. Post-Fix Verification** | Re-running `ipconfig /renew`, ping test to server, closing the incident ticket. |

---

## 🎬 Step-by-Step Demonstration Script

### Phase 1: The Broken Scenario (`NET-010`)
- **Topology**:
  - `PC1` in **VLAN 10** (`192.168.10.0/24`) connected to `Switch-1` access port `Fa0/1`.
  - `Switch-1` connected via 802.1Q trunk to `Router-1` interface `GigabitEthernet0/0`.
  - `Router-1` uses subinterface `GigabitEthernet0/0.10` (`192.168.10.1/24`).
  - Central DHCP Server (`192.168.50.2`) located in Server Farm **VLAN 50** (`Gig0/0.50`).
- **Symptom**:
  - `PC1` fails to obtain an IP address from DHCP.
  - Windows `ipconfig` outputs APIPA address: `169.254.12.88 / 255.255.0.0`.
  - User cannot reach any local or remote network resources.

---

### Phase 2: Evidence Collection & Show Commands
The junior engineer captures the following Cisco IOS outputs from Packet Tracer:

```text
Router-1# show running-config interface GigabitEthernet0/0.10
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0

Router-1# ping 192.168.50.2
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 192.168.50.2, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5)
```

---

### Phase 3: Automated Diagnostic Execution

#### 1. Python Deterministic Rule Checker
NetSage AI's rule checker parses the show output before AI execution and flags:
- **Rule ID**: `RULE-L3-014`
- **Detection**: *Missing IP Helper-Address for DHCP Relay*
- **Evidence Quoted**: `Router-1 subinterface running-config lacks 'ip helper-address <server_ip>'`
- **Severity**: High | Layer: Layer 3

#### 2. NetSage AI Diagnosis Output
```json
{
  "case_id": "NET-010",
  "root_cause": "Router-1 subinterface GigabitEthernet0/0.10 is missing 'ip helper-address 192.168.50.2'. DHCP broadcast discover packets cannot cross broadcast domains without a configured relay agent.",
  "osi_layer": "Layer 3",
  "confidence": "High",
  "confidence_score": 0.94,
  "evidence": [
    "Router-1 GigabitEthernet0/0.10 running-config lacks 'ip helper-address 192.168.50.2'",
    "Router-1 can successfully ping DHCP server 192.168.50.2 with 100% success rate"
  ],
  "next_command": "show running-config interface GigabitEthernet0/0.10",
  "fix_steps": [
    "Router-1(config)# interface GigabitEthernet0/0.10",
    "Router-1(config-subif)# ip helper-address 192.168.50.2",
    "Router-1(config-subif)# exit"
  ],
  "human_review_required": true,
  "safety_risk": "Low"
}
```

---

### Phase 4: Mandatory Human Review Gate
1. The senior network engineer reviews the AI recommendation on the NetSage AI Web Console.
2. **Reviewer Checklist**:
   - [x] Quoted evidence is verbatim from the router config.
   - [x] Layer 3 attribution is accurate.
   - [x] Proposed commands do not disrupt other VLANs.
3. **Verdict**: **ACCEPTED**.
4. The engineer signs off with note: *"Verified DHCP server IP 192.168.50.2 is reachable from Router-1. Fix approved."*

---

### Phase 5: Cisco IOS Fix Application
Paste the approved commands into `Router-1` CLI in Packet Tracer:

```cisco
Router-1# configure terminal
Router-1(config)# interface GigabitEthernet0/0.10
Router-1(config-subif)# ip helper-address 192.168.50.2
Router-1(config-subif)# end
Router-1# write memory
```

---

### Phase 6: End-to-End Verification

1. **On Client PC1**:
   ```text
   PC1> ipconfig /renew
   IP Address......................: 192.168.10.25
   Subnet Mask.....................: 255.255.255.0
   Default Gateway.................: 192.168.10.1
   DNS Servers.....................: 192.168.50.2
   ```

2. **Connectivity Test**:
   ```text
   PC1> ping 192.168.50.2
   Pinging 192.168.50.2 with 32 bytes of data:
   Reply from 192.168.50.2: bytes=32 time=12ms TTL=127
   Reply from 192.168.50.2: bytes=32 time=11ms TTL=127
   Ping statistics: 4 packets transmitted, 4 received, 0% packet loss.
   ```

3. **Status**: **RESOLVED & VERIFIED**.