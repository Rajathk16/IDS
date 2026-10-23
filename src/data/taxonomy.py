"""Official CICIoT2023 dataset taxonomy and label mapping utilities."""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

# Official 46 numerical flow features in CICIoT2023
CICIOT2023_FEATURE_NAMES: List[str] = [
    "flow_duration",
    "Header_Length",
    "Protocol Type",
    "Duration",
    "Rate",
    "Srate",
    "Drate",
    "fin_flag_number",
    "syn_flag_number",
    "rst_flag_number",
    "psh_flag_number",
    "ack_flag_number",
    "ece_flag_number",
    "cwr_flag_number",
    "ack_count",
    "syn_count",
    "fin_count",
    "urg_count",
    "rst_count",
    "HTTP",
    "HTTPS",
    "DNS",
    "Telnet",
    "SMTP",
    "SSH",
    "IRC",
    "TCP",
    "UDP",
    "DHCP",
    "ARP",
    "ICMP",
    "IPv",
    "LLC",
    "Tot sum",
    "Min",
    "Max",
    "AVG",
    "Std",
    "Tot size",
    "IAT",
    "Number",
    "Magnitue",  # Official dataset spelling
    "Radius",
    "Covariance",
    "Variance",
    "Weight"
]

# Canonical mapping from 34 specific CICIoT2023 labels to 8 High-Level Categories
CICIOT2023_CATEGORY_MAPPING: Dict[str, str] = {
    # Benign
    "BenignTraffic": "Benign",
    "benign": "Benign",
    
    # DDoS (12 attack types)
    "DDoS-RSTFINFlood": "DDoS",
    "DDoS-PSHACK_Flood": "DDoS",
    "DDoS-SYN_Flood": "DDoS",
    "DDoS-UDP_Flood": "DDoS",
    "DDoS-TCP_Flood": "DDoS",
    "DDoS-ICMP_Flood": "DDoS",
    "DDoS-SynonymousIP_Flood": "DDoS",
    "DDoS-ACK_Fragmentation": "DDoS",
    "DDoS-UDP_Fragmentation": "DDoS",
    "DDoS-ICMP_Fragmentation": "DDoS",
    "DDoS-SlowLoris": "DDoS",
    "DDoS-HTTP_Flood": "DDoS",
    
    # DoS (4 attack types)
    "DoS-UDP_Flood": "DoS",
    "DoS-TCP_Flood": "DoS",
    "DoS-SYN_Flood": "DoS",
    "DoS-HTTP_Flood": "DoS",
    
    # Reconnaissance & Scanning (5 attack types)
    "Recon-HostDiscovery": "Recon",
    "Recon-OSScan": "Recon",
    "Recon-PortScan": "Recon",
    "Recon-PingSweep": "Recon",
    "VulnerabilityScan": "Recon",
    
    # Web & Injection (6 attack types)
    "SqlInjection": "Web",
    "CommandInjection": "Web",
    "XSS": "Web",
    "Backdoor_Malware": "Web",
    "BrowserHijacking": "Web",
    "Uploading_Attack": "Web",
    
    # Brute Force (1 attack type)
    "DictionaryBruteForce": "BruteForce",
    
    # Spoofing / MITM (2 attack types)
    "MITM-ArpSpoofing": "Spoofing",
    "DNS_Spoofing": "Spoofing",
    
    # Mirai Botnet (3 attack types)
    "Mirai-greeth_flood": "Mirai",
    "Mirai-udpplain": "Mirai",
    "Mirai-greip_flood": "Mirai",
}


def map_to_binary(raw_label: str) -> str:
    """Map any raw dataset label to 'BENIGN' or 'ATTACK'."""
    clean = str(raw_label).strip()
    if clean.lower() in ("benigntraffic", "benign", "normal", "0"):
        return "BENIGN"
    return "ATTACK"


def map_to_category(raw_label: str) -> str:
    """Map any raw dataset label to one of the 8 high-level categories."""
    clean = str(raw_label).strip()
    if clean in CICIOT2023_CATEGORY_MAPPING:
        return CICIOT2023_CATEGORY_MAPPING[clean]
    # Case-insensitive fallback
    for k, v in CICIOT2023_CATEGORY_MAPPING.items():
        if k.lower() == clean.lower():
            return v
    if "ddos" in clean.lower():
        return "DDoS"
    if "dos" in clean.lower():
        return "DoS"
    if "mirai" in clean.lower():
        return "Mirai"
    if "recon" in clean.lower() or "scan" in clean.lower():
        return "Recon"
    if "injection" in clean.lower() or "web" in clean.lower():
        return "Web"
    if "spoof" in clean.lower() or "mitm" in clean.lower():
        return "Spoofing"
    if "brute" in clean.lower():
        return "BruteForce"
    if clean.lower() in ("benigntraffic", "benign"):
        return "Benign"
    return "Unknown_Attack"


def get_supported_categories() -> List[str]:
    """Return ordered list of 8 supported categories."""
    return ["Benign", "DDoS", "DoS", "Recon", "Web", "BruteForce", "Spoofing", "Mirai"]
