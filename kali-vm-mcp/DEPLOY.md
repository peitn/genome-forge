# Deployment

## Živá infrastruktura

| Komponenta | URL |
|---|---|
| **MCP endpoint (CF Worker brána)** | `https://kali-mcp-gateway.alena-rejdova.workers.dev/mcp` |
| **MCP SSE direct (HF Space)** | `https://peiti-kali-mcp-server.hf.space/sse` |
| **HF Space dashboard** | `https://huggingface.co/spaces/peiti/kali-mcp-server` |

## Přidat do Claude (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "kali-vm": {
      "url": "https://kali-mcp-gateway.alena-rejdova.workers.dev/mcp"
    }
  }
}
```

## Architektura

```
Claude
  │
  │  HTTPS/SSE
  ▼
Cloudflare Worker (brána)
https://kali-mcp-gateway.alena-rejdova.workers.dev
  │
  │  proxy
  ▼
HuggingFace Space (MCP server)
https://peiti-kali-mcp-server.hf.space
  │
  │  PHANTOM_AUTH_TOKEN
  ▼
Cloudflare Worker (secrets)
https://phantom-secrets.alena-rejdova.workers.dev
  │
  ├── GEMINI_API_KEY
  ├── HF_TOKEN
  └── ...
```

## Dostupné nástroje (remote)

- `gemini_chat` — Chat s Gemini AI
- `gemini_analyze_image` — Analýza obrázku Gemini Vision
- `gemini_generate_code` — Generování kódu
- `hf_inference` — Inference na HF modelu
- `hf_search_models` — Hledání modelů na HF Hub

## Lokální VM server (`server.py`)

Pro ovládání Kali Linux VM (VirtualBox) spusť lokálně:

```bash
export PHANTOM_AUTH_TOKEN=pat_...
pip install mcp requests
python3 kali-vm-mcp/server.py
```
