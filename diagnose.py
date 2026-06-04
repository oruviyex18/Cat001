import paramiko, sys

HOST = "212.67.13.125"
USER = "root"
PASSWORD = "hVwdLNk5&YFo"

def run(client, label, cmd):
    print(f"\n>>> {label}")
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    if out.strip(): print(out.strip())
    if err.strip(): print("[stderr]", err.strip())

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD, timeout=15)

run(client, "List /opt/cat001/frontend/", "ls /opt/cat001/frontend/")
run(client, "Check package.json", "ls -la /opt/cat001/frontend/package*.json 2>&1 || echo NOT FOUND")
run(client, "Git log", "cd /opt/cat001 && git log --oneline -3")
run(client, "Git status", "cd /opt/cat001 && git status --short")
run(client, "Check .gitignore for package", "cd /opt/cat001 && git ls-files frontend/package.json frontend/package-lock.json")

client.close()
