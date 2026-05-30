FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    curl wget git vim nano \
    nmap netcat-traditional netcat-openbsd \
    net-tools iputils-ping dnsutils \
    whois traceroute \
    hydra sqlmap \
    metasploit-framework \
    john hashcat \
    aircrack-ng \
    tcpdump wireshark-common \
    gobuster dirb nikto \
    openssh-client \
    zip unzip tar jq tree htop \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    "mcp>=1.0.0" \
    "requests>=2.31.0" \
    "starlette>=0.40.0" \
    "uvicorn[standard]>=0.30.0"

RUN mkdir -p /workspace /data

WORKDIR /app
COPY app.py .

EXPOSE 7860
CMD ["python3", "app.py"]
