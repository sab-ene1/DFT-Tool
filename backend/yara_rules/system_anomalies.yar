rule SystemModification {
    meta:
        description = "Detects system modification attempts"
        author = "Forensics Tool"
        date = "2023-12-04"
        
    strings:
        $reg_edit = "regedit" nocase
        $sys_mod = "system32" nocase
        $driver_mod = "drivers" nocase
        $service_mod = "services.exe" nocase
        
    condition:
        2 of them
}

rule NetworkAnomaly {
    meta:
        description = "Detects suspicious network activity"
        author = "Forensics Tool"
        date = "2023-12-04"
        
    strings:
        $port_scan = "nmap" nocase
        $netcat = "nc.exe" nocase
        $wireshark = "wireshark" nocase
        $tcpdump = "tcpdump" nocase
        
    condition:
        any of them
}

rule UnauthorizedAccess {
    meta:
        description = "Detects potential unauthorized access attempts"
        author = "Forensics Tool"
        date = "2023-12-04"
        
    strings:
        $rdp = "mstsc.exe" nocase
        $telnet = "telnet" nocase
        $ssh = "putty" nocase
        $vnc = "vncviewer" nocase
        
    condition:
        any of them
}
