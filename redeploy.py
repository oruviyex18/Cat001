import paramiko, sys

HOST = "212.67.13.125"
USER = "root"
PASSWORD = "hVwdLNk5&YFo"

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

run(client, "Pull latest code", "cd /opt/cat001 && git pull")
run(client, "Verify package.json exists", "ls /opt/cat001/frontend/package.json")
run(client, "Build and start (this takes a few minutes)", "cd /opt/cat001 && docker compose up --build -d 2>&1", timeout=600)
run(client, "Container status", "cd /opt/cat001 && docker compose ps 2>&1")
run(client, "Backend logs (last 20)", "cd /opt/cat001 && docker compose logs backend --tail 20 2>&1")

client.close()
print("\nDone. Visit http://212.67.13.125")
