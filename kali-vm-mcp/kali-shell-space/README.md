# Kali Linux Shell MCP — HuggingFace Space

Plný Kali Linux přes MCP SSE endpoint.

## Živé URL

| Co | URL |
|---|---|
| **MCP endpoint (doporučeno)** | `https://kali-mcp-gateway.alena-rejdova.workers.dev/kali` |
| **HF Space přímá** | `https://peiti-kali-shell-mcp.hf.space/sse` |
| **HF Space dashboard** | `https://huggingface.co/spaces/peiti/kali-shell-mcp` |
| **Gemini AI endpoint** | `https://kali-mcp-gateway.alena-rejdova.workers.dev/ai` |

## Přidat do Claude

```json
{
  "mcpServers": {
    "kali": {
      "url": "https://kali-mcp-gateway.alena-rejdova.workers.dev/kali"
    }
  }
}
```

## Dostupné nástroje

### Shell
- `shell` — spusti libovolný bash příkaz (root přístup)
- `shell_interactive` — příkaz + exit code + oddělený stdout/stderr

### Filesystem
- `file_read` — přečti soubor
- `file_write` — vytvoř/přepiš soubor
- `file_list` — výpis adresáře
- `file_delete` — smaž soubor/adresář

### Systém
- `system_info` — OS, CPU, RAM, disk
- `process_list` — běžící procesy
- `network_info` — síťová rozhraní, IP, routy

### Správa balíčků
- `pkg_install` — apt-get install
- `pkg_search` — apt-cache search

### ProtonVPN
- `vpn_install` — nainstaluje ProtonVPN CLI
- `vpn_connect` — připojí VPN
- `vpn_disconnect` — odpojí VPN
- `vpn_status` — stav připojení

### Kali nástroje (shortcuts)
- `nmap_scan` — network scan
- `whois_lookup` — whois
- `dns_lookup` — DNS záznamy

### Předinstalované nástroje
```
nmap, metasploit-framework, hydra, sqlmap, burpsuite,
john, hashcat, aircrack-ng, nikto, gobuster, dirb,
tcpdump, wireshark-common, netcat, curl, wget, git...
```

## Poznámky
- Workspace: `/workspace` (pracovní adresář)
- Kontejner běží jako root
- ProtonVPN může vyžadovat NET_ADMIN capability (záleží na HF Space)
