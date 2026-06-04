import paramiko
import time
import sys

HOST = "212.67.13.125"
USER = "root"
PASSWORD = "hVwdLNk5&YFo"

ENV_CONTENT = """DJANGO_SECRET_KEY=prod-secret-$(openssl rand -hex 32)
DEBUG=False
POSTGRES_USER=catuser
POSTGRES_PASSWORD=catpass
POSTGRES_DB=catdb
DATABASE_URL=postgres://catuser:catpass@db:5432/catdb
ALLOWED_HOSTS=localhost,127.0.0.1,backend,212.67.13.125
FRONTEND_URL=http://212.67.13.125
REDIS_URL=redis://redis:6379/0
"""

COMMANDS = [
    ("Update apt package list", "apt-get update -qq"),
    ("Install Docker dependencies", "apt-get install -y -qq ca-certificates curl gnupg lsb-release"),
    ("Add Docker GPG key", "install -m 0755 -d /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && chmod a+r /etc/apt/keyrings/docker.gpg"),
    ("Add Docker apt repo", 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null'),
    ("Install Docker Engine", "apt-get update -qq && apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"),
    ("Verify Docker", "docker --version && docker compose version"),
    ("Clone repository", "[ -d /opt/cat001 ] && git -C /opt/cat001 pull || git clone https://github.com/oruviyex18/Cat001.git /opt/cat001"),
    ("Write .env file", f"cat > /opt/cat001/.env << 'ENVEOF'\n{ENV_CONTENT}ENVEOF"),
    ("Fix secret key", "SECRET=$(openssl rand -hex 32) && sed -i \"s|prod-secret-\\$(openssl rand -hex 32)|$SECRET|\" /opt/cat001/.env"),
    ("Build and start containers", "cd /opt/cat001 && docker compose up --build -d"),
    ("Check container status", "cd /opt/cat001 && docker compose ps"),
    ("Check backend logs", "cd /opt/cat001 && docker compose logs backend --tail 15"),
]

def run(client, label, cmd, timeout=300):
    print(f"\n>>> {label}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.strip().encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    if err.strip():
        print("[stderr]", err.strip().encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    if code != 0:
        print(f"[!] Exit code {code} — continuing...")
    return code

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print(f"Connecting to {HOST}...")
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("Connected.")

for label, cmd in COMMANDS:
    run(client, label, cmd, timeout=600)

client.close()
print("\nDeployment complete. Visit http://212.67.13.125")
