import paramiko, sys

HOST = "212.67.13.125"
USER = "root"
PASSWORD = "hVwdLNk5&YFo"
DOMAIN = "mycat.onthewifi.com"
EMAIL = "leo7g@protonmail.com"

def run(client, label, cmd, timeout=600):
    print(f"\n>>> {label}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    code = stdout.channel.recv_exit_status()
    if out.strip(): print(out.strip())
    if err.strip(): print("[stderr]", err.strip())
    if code != 0:
        print(f"[!] Exit code {code}")
    return code

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print("Connected.")

# Stop current stack (frees port 80 for certbot standalone)
run(client, "Stop all containers", "cd /opt/cat001 && docker compose down")

# Create the named volumes that docker compose will later use
run(client, "Create certbot volumes", "docker volume create cat001_certbot_conf; docker volume create cat001_certbot_www")

# Issue certificate using certbot standalone (takes over port 80 temporarily)
run(client, "Issue Let's Encrypt certificate (standalone)",
    f"docker run --rm -p 80:80 "
    f"-v cat001_certbot_conf:/etc/letsencrypt "
    f"-v cat001_certbot_www:/var/www/certbot "
    f"certbot/certbot certonly --standalone "
    f"-d {DOMAIN} "
    f"--email {EMAIL} "
    f"--agree-tos --no-eff-email",
    timeout=120)

# Verify cert was issued
run(client, "Verify certificate files",
    f"docker run --rm -v cat001_certbot_conf:/etc/letsencrypt certbot/certbot certificates")

# Pull latest code (nginx.conf with HTTPS, updated docker-compose)
run(client, "Pull latest code", "cd /opt/cat001 && git pull")

# Update .env with domain-specific values
run(client, "Update .env for domain",
    f"sed -i 's|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=localhost,127.0.0.1,backend,212.67.13.125,{DOMAIN}|' /opt/cat001/.env && "
    f"sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://{DOMAIN}|' /opt/cat001/.env && "
    "cat /opt/cat001/.env | grep -E 'ALLOWED_HOSTS|FRONTEND_URL'")

# Add cron job for cert renewal + nginx reload
run(client, "Add renewal cron job",
    "echo '0 3 * * * cd /opt/cat001 && docker compose run --rm certbot renew --quiet && docker compose restart frontend' "
    "| crontab -")

# Rebuild and start everything
run(client, "Build and start stack", "cd /opt/cat001 && docker compose up --build -d", timeout=600)

# Wait a moment for containers to initialize
run(client, "Wait for startup", "sleep 10")

# Check status
run(client, "Container status", "cd /opt/cat001 && docker compose ps 2>&1")
run(client, "Backend logs", "cd /opt/cat001 && docker compose logs backend --tail 10 2>&1")

client.close()
print(f"\nDone. Site is live at https://{DOMAIN}")
