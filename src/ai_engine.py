"""
NetSage AI - AI Diagnostic Engine
Performs evidence-backed root cause analysis using structured prompts and returns parseable JSON diagnoses.

Supports a live LLM call (Groq free tier, via GROQ_API_KEY) with automatic, graceful
fallback to a deterministic offline reasoning engine when no key is configured, the call fails,
a rate limit is hit, or the model's response can't be parsed into the required schema. The app
never breaks because of the AI call: it always returns a valid diagnosis.
"""

import os
import json
import re
import time
from typing import Dict, Any, List, Optional
from src.rule_checker import NetworkRuleChecker

try:
    import requests
except ImportError:  # requests is optional; only needed for the live AI path
    requests = None

REQUIRED_LAYERS = {"Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"}
REQUIRED_CONFIDENCE = {"High", "Medium", "Low"}


class DiagnosticEngine:
    def __init__(self, prompt_path: str = None):
        if not prompt_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            prompt_path = os.path.join(base_dir, "prompts", "diagnose_prompt.md")
        self.prompt_path = prompt_path
        self.rule_checker = NetworkRuleChecker()
        self._load_prompt_template()

        # Live AI configuration (Groq free tier - no credit card required).
        # Get a free key at https://console.groq.com/keys (starts with "gsk_")
        # and set it as an environment variable named GROQ_API_KEY. If it's
        # not set, NetSage AI automatically runs on the deterministic
        # offline reasoning engine instead.
        #
        # Default model: Groq deprecated llama-3.3-70b-versatile (shut down
        # August 16, 2026) and officially recommends openai/gpt-oss-120b as
        # its replacement. If Groq's catalog changes again in the future,
        # override with the GROQ_MODEL environment variable rather than
        # editing this file -- see console.groq.com/docs/deprecations for
        # the current migration guidance.
        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b").strip()
        self.use_live_ai = bool(self.api_key) and requests is not None
        self.last_error: Optional[str] = None

    def _load_prompt_template(self):
        if os.path.exists(self.prompt_path):
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = "NetSage AI Tier-3 Network Diagnostic Assistant."

    def diagnose(self, case_id: str, symptom: str, topology_note: str, show_outputs: str, simulate_ai_error: bool = False) -> Dict[str, Any]:
        """
        Diagnoses a network troubleshooting case.
        Returns a structured JSON response matching the required schema.
        """
        # Run rule checker to gather deterministic facts
        rule_findings = self.rule_checker.analyze(symptom, topology_note, show_outputs)

        # Check if this case is one of the designated Responsible AI failure simulation cases
        if simulate_ai_error:
            error_diag = self._get_simulated_ai_error(case_id, symptom, topology_note, show_outputs)
            if error_diag:
                return error_diag

        # Try a live Groq call first if a key is configured; fall back safely on any failure.
        if self.use_live_ai:
            self.last_error = None
            live_diag = self._call_groq(case_id, symptom, topology_note, show_outputs)
            if live_diag is not None:
                return live_diag
            # Live call failed or returned something unusable - fall through to offline engine.

        # Offline High-Fidelity Network Reasoning Engine (also the default / no-API-key path)
        offline_diag = self._generate_accurate_diagnosis(case_id, symptom, topology_note, show_outputs, rule_findings)
        offline_diag["ai_source"] = "offline_reasoning_engine"
        if self.use_live_ai and self.last_error:
            offline_diag["ai_fallback_reason"] = self.last_error
        return offline_diag

    # ------------------------------------------------------------------
    # Live AI (Groq free tier)
    # ------------------------------------------------------------------
    def _call_groq(self, case_id: str, symptom: str, topology_note: str, show_outputs: str) -> Optional[Dict[str, Any]]:
        """
        Calls the Groq API (OpenAI-compatible chat completions) using the
        project's diagnose_prompt.md as the system message, requests strict
        JSON output, and validates/normalizes the response into NetSage AI's
        required schema.

        Returns None (never raises) on any failure so the caller can fall back to
        the deterministic engine - the app must never crash because a free API
        rate-limited or timed out.
        """
        user_prompt = (
            f"Case ID: {case_id}\n\n"
            f"Symptom:\n{symptom}\n\n"
            f"Topology Note:\n{topology_note}\n\n"
            f"Show Command Output:\n{show_outputs}\n\n"
            "Diagnose this case. Respond with ONLY the JSON object described in the "
            "system instructions - no markdown fences, no commentary."
        )

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=25)
        except requests.exceptions.RequestException as e:
            self.last_error = f"network_error: {e}"
            return None

        if resp.status_code == 429:
            self.last_error = "rate_limited: Groq free-tier request/day or token/min limit reached"
            return None
        if resp.status_code == 401:
            self.last_error = "auth_error: GROQ_API_KEY is missing or invalid (check it starts with 'gsk_')"
            return None
        if resp.status_code != 200:
            self.last_error = f"http_{resp.status_code}: {resp.text[:200]}"
            return None

        try:
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            self.last_error = f"unexpected_response_shape: {e}"
            return None

        parsed = self._parse_model_json(raw_text)
        if parsed is None:
            self.last_error = "json_parse_failed"
            return None
    
        return self._normalize_live_diagnosis(case_id, parsed)

    @staticmethod
    def _parse_model_json(raw_text: str) -> Optional[Dict[str, Any]]:
        """Strips accidental markdown fences and parses the model's JSON output."""
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _normalize_live_diagnosis(self, case_id: str, parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validates the model's JSON against the required schema and fills in safe
        defaults for anything missing or malformed. Returns None if the response
        is too broken to salvage, so the caller falls back to the offline engine.
        """
        try:
            osi_layer = parsed.get("osi_layer", "Layer 3")
            if osi_layer not in REQUIRED_LAYERS:
                osi_layer = "Layer 3"

            confidence = parsed.get("confidence", "Medium")
            if confidence not in REQUIRED_CONFIDENCE:
                confidence = "Medium"

            confidence_score = parsed.get("confidence_score", 0.7)
            try:
                confidence_score = float(confidence_score)
            except (TypeError, ValueError):
                confidence_score = 0.7

            evidence = parsed.get("evidence") or []
            if not isinstance(evidence, list) or not evidence:
                evidence = ["Model did not cite specific evidence; human review required."]

            fix_steps = parsed.get("fix_steps") or []
            if not isinstance(fix_steps, list) or not fix_steps:
                fix_steps = ["No fix commands returned by model; human reviewer must determine remediation."]

            verification_steps = parsed.get("verification_steps") or []
            if not isinstance(verification_steps, list) or not verification_steps:
                verification_steps = ["Manually verify the proposed root cause before applying any fix."]

            root_cause = str(parsed.get("root_cause", "")).strip()
            if not root_cause:
                return None  # Too little to salvage - let the caller fall back.

            return {
                "case_id": case_id,
                "root_cause": root_cause,
                "osi_layer": osi_layer,
                "confidence": confidence,
                "confidence_score": confidence_score,
                "evidence": evidence,
                "rationale": parsed.get("rationale", ""),
                "next_command": parsed.get("next_command", "show ip interface brief"),
                "fix_steps": fix_steps,
                  "verification_steps": verification_steps,
                # Safety rule is non-negotiable regardless of what the model returns.
                "human_review_required": True,
                "safety_risk": parsed.get("safety_risk", "Medium"),
                "ai_source": "groq_live",
            }
        except Exception as e:
            self.last_error = f"normalize_error: {e}"
            return None

    def _generate_accurate_diagnosis(self, case_id: str, symptom: str, topology: str, show: str, rule_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates evidence-backed structured diagnosis."""
        primary_finding = rule_findings[0] if rule_findings else None
        
        # Determine Layer and Category
        layer = primary_finding["osi_layer"] if primary_finding else "Layer 3"
        
        # Build evidence quotes
        evidence_list = []
        if primary_finding:
            evidence_list.append(primary_finding["evidence"])
        
        # Add matching lines from show outputs
        for line in show.splitlines():
            line_s = line.strip()
            if any(k in line_s.lower() for k in ["mismatch", "inactive", "administratively down", "dropped", "timed out", "unreachable", "flapping", "utilization", "100%", "down"]):
                if line_s not in evidence_list and len(evidence_list) < 3:
                    evidence_list.append(line_s)
                    
        if not evidence_list:
            evidence_list.append("Show command outputs reveal configuration state divergence from topology intent.")

        # Construct diagnosis
        if primary_finding:
            root_cause = f"{primary_finding['name']}: {primary_finding['explanation']}"
            fix_steps = [s.strip() for s in primary_finding["suggested_fix"].split("\n") if s.strip()]
            confidence = "High"
            confidence_score = 0.94
        else:
            root_cause = f"Configuration fault identified in {symptom}"
            fix_steps = ["Inspect interface configuration and routing table entries."]
            confidence = "Medium"
            confidence_score = 0.75

        # Suggest next verification command
        next_cmd = "show ip interface brief"
        if "vlan" in symptom.lower() or layer == "Layer 2":
            next_cmd = "show interfaces trunk"
        elif "ospf" in symptom.lower():
            next_cmd = "show ip ospf neighbor"
        elif "dhcp" in symptom.lower():
            next_cmd = "show ip dhcp binding"
        elif "acl" in symptom.lower() or "access" in symptom.lower():
            next_cmd = "show ip access-lists"
        elif "nat" in symptom.lower():
            next_cmd = "show ip nat translations"

        return {
            "case_id": case_id,
            "root_cause": root_cause,
            "osi_layer": layer,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "evidence": evidence_list,
            "rationale": f"Analysis of symptom '{symptom}' correlates with deterministic show command findings. The fault directly prevents packet forwarding at {layer}.",
            "next_command": next_cmd,
            "fix_steps": fix_steps,
            "verification_steps": [
                f"Execute '{next_cmd}' to verify operational state.",
                "Execute end-to-end ICMP ping between source host and target destination to confirm reachability."
            ],
            "human_review_required": True,
            "safety_risk": "Low" if layer in ["Layer 1", "Layer 7"] else "Medium"
        }

    def _get_simulated_ai_error(self, case_id: str, symptom: str, topo: str, show: str) -> Dict[str, Any]:
        """
        Simulates subtle AI failure modes (hallucinations, unsafe commands, asymmetric blindspots, wrong layer)
        for the 6 documented Responsible AI cases.
        """
        # Simulated Failure 1: Case NET-022 (Asymmetric Routing mistaken for ACL block)
        if case_id == "NET-022":
            return {
                "case_id": "NET-022",
                "root_cause": "[AI ERROR - Overconfidence / Misattribution] The firewall or access list on Router-A is silently dropping ICMP echo replies from Site-B Server.",
                "osi_layer": "Layer 4",
                "confidence": "High",
                "confidence_score": 0.91,
                "evidence": [
                    "Router-A show ip route has valid route to 10.20.30.0/24",
                    "Site-A PC sends packets but never receives replies"
                ],
                "rationale": "Since Router-A has a route to the destination, the forward path is clear. The failure to receive responses is likely due to an inbound ACL on Router-A or Server firewall.",
                "next_command": "Router-A# show ip access-lists",
                "fix_steps": [
                    "Router-A(config)# ip access-list extended ALLOW_ALL",
                    "Router-A(config-ext-nacl)# permit ip any any",
                    "Router-A(config)# interface GigabitEthernet0/0",
                    "Router-A(config-if)# ip access-group ALLOW_ALL in"
                ],
                "verification_steps": ["Site-A# ping 10.20.30.100"],
                "human_review_required": True,
                "safety_risk": "High",
                "simulated_failure_type": "Asymmetric Routing Blindspot & Unsafe ACL Permissive Override"
            }

        # Simulated Failure 2: Case NET-005 (Hallucinated non-existent interface and wrong command)
        if case_id == "NET-005":
            return {
                "case_id": "NET-005",
                "root_cause": "[AI ERROR - Hallucination & Destructive Command] Switchport Fa0/24 needs to be converted into a routed port by disabling switchport mode.",
                "osi_layer": "Layer 3",
                "confidence": "High",
                "confidence_score": 0.88,
                "evidence": [
                    "Administrative Mode: dynamic auto",
                    "Operational Mode: static access"
                ],
                "rationale": "Disabling switchport and configuring an IP address on GigabitEthernet0/99 will establish routing between switches.",
                "next_command": "Switch-A# show interfaces GigabitEthernet0/99 status",
                "fix_steps": [
                    "Switch-A(config)# interface FastEthernet0/24",
                    "Switch-A(config-if)# no switchport",
                    "Switch-A(config-if)# ip address 10.99.99.1 255.255.255.0",
                    "Switch-A(config)# interface GigabitEthernet0/99",
                    "Switch-A(config-if)# no shutdown"
                ],
                "verification_steps": ["Switch-A# show ip interface brief"],
                "human_review_required": True,
                "safety_risk": "Critical",
                "simulated_failure_type": "Hallucinated Interface & Destructive L2/L3 Command"
            }

        # Simulated Failure 3: Case NET-015 (Misdiagnosed DHCP timeout as Layer 7 DNS server crash)
        if case_id == "NET-015":
            return {
                "case_id": "NET-015",
                "root_cause": "[AI ERROR - Wrong Layer Attribution] The DNS Server service at 192.168.1.200 has crashed and requires service restart on port 53.",
                "osi_layer": "Layer 7",
                "confidence": "High",
                "confidence_score": 0.93,
                "evidence": [
                    "*** Can't find address for server 192.168.1.200: Timed out",
                    "PC-1 can ping 93.184.216.34"
                ],
                "rationale": "Because the host has internet IP connectivity, the DNS server daemon on 192.168.1.200 must have failed or stopped listening on UDP port 53.",
                "next_command": "DNS-Server# show processes cpu | include named",
                "fix_steps": [
                    "On DNS Server: Restart DNS service and bind to 192.168.1.200",
                    "PC-1> ipconfig /flushdns"
                ],
                "verification_steps": ["PC-1> nslookup www.example.com"],
                "human_review_required": True,
                "safety_risk": "Medium",
                "simulated_failure_type": "Failure to check active IP topology (192.168.1.200 does not exist)"
            }

        # Simulated Failure 4: Case NET-033 (Wireless guest isolation breach blamed on Wi-Fi password)
        if case_id == "NET-033":
            return {
                "case_id": "NET-033",
                "root_cause": "[AI ERROR - Misdiagnosis / Incomplete Evidence] Guest users are connecting with corporate WPA2 credentials rather than guest splash portal.",
                "osi_layer": "Layer 2",
                "confidence": "Medium",
                "confidence_score": 0.65,
                "evidence": [
                    "WLAN ID 2 Guest-Access / Company-Guest Enabled",
                    "Guest Wi-Fi users can ping internal accounting servers"
                ],
                "rationale": "Guests should not have access to WPA2 corporate pre-shared keys. The AP needs PSK rotation.",
                "next_command": "WLC-1# show wlan 2",
                "fix_steps": [
                    "WLC-1(config)# wlan 2",
                    "WLC-1(config-wlan)# security wpa akm 802.1x",
                    "WLC-1(config-wlan)# end"
                ],
                "verification_steps": ["WLC-1# show wlan summary"],
                "human_review_required": True,
                "safety_risk": "High",
                "simulated_failure_type": "Security Policy Misdiagnosis (ignored VLAN 1 interface mapping)"
            }

        # Simulated Failure 5: Case NET-001 (Native VLAN mismatch fix proposed without checking STP)
        if case_id == "NET-001":
            return {
                "case_id": "NET-001",
                "root_cause": "[AI ERROR - Dangerous Remediation] Switch-B trunk native VLAN 99 is invalid. Native VLAN should always be forced to VLAN 1 on all switches.",
                "osi_layer": "Layer 2",
                "confidence": "High",
                "confidence_score": 0.89,
                "evidence": [
                    "Switch-A# show interfaces trunk: Native vlan 1",
                    "Switch-B# show interfaces trunk: Native vlan 99"
                ],
                "rationale": "VLAN 1 is the default Cisco management VLAN. Any trunk using a non-default native VLAN violates standard baseline.",
                "next_command": "Switch-B# show vlan brief",
                "fix_steps": [
                    "Switch-B(config)# interface GigabitEthernet0/1",
                    "Switch-B(config-if)# no switchport trunk native vlan",
                    "Switch-B(config-if)# exit"
                ],
                "verification_steps": ["Switch-B# show interfaces trunk"],
                "human_review_required": True,
                "safety_risk": "Medium",
                "simulated_failure_type": "Violation of Security Best Practices (VLAN 1 Native VLAN Prone to Hopping)"
            }

        # Simulated Failure 6: Case NET-028 (Inverted wildcard mask misunderstood)
        if case_id == "NET-028":
            return {
                "case_id": "NET-028",
                "root_cause": "[AI ERROR - Incomplete Mask Parsing] The ACL rule is inactive because interface G0/1 has not enabled ip routing.",
                "osi_layer": "Layer 3",
                "confidence": "Medium",
                "confidence_score": 0.70,
                "evidence": [
                    "ACL 110 line 10 deny ip 192.168.20.0 255.255.255.0 host 10.0.0.5",
                    "20 permit ip any any (241 matches)"
                ],
                "rationale": "The router is permitting all traffic because IP routing table is bypassed.",
                "next_command": "Router-1# show ip route",
                "fix_steps": [
                    "Router-1(config)# ip routing",
                    "Router-1(config)# interface GigabitEthernet0/1",
                    "Router-1(config-if)# ip access-group 110 in"
                ],
                "verification_steps": ["Router-1# show ip access-lists 110"],
                "human_review_required": True,
                "safety_risk": "Medium",
                "simulated_failure_type": "Missed wildcard mask inversion error"
            }

        return None