import os
import subprocess
import sys
import re
import termios
import tty
import select
import time
import requests
import signal
import socket

# 𝗠𝗮𝗻𝗮𝗴𝗲𝗱 𝗕𝘆 @Nactire

def print_green(text):
    print("\033[1;32m" + text + "\033[0m")

def print_red(text):
    print("\033[1;31m" + text + "\033[0m")
    
def print_yellow(text):
    print("\033[1;33m" + text + "\033[0m")

def run_command(cmd):
    process = subprocess.Popen(cmd, shell=True)
    process.wait()
    return process.returncode

def is_installed(cmd):
    return subprocess.call(f"{cmd} > /dev/null 2>&1", shell=True) == 0
    
def is_certbot_nginx_plugin_installed():
    try:
        result = subprocess.check_output(
            "dpkg -l | grep python3-certbot-nginx", shell=True, text=True
        )
        return "python3-certbot-nginx" in result
    except subprocess.CalledProcessError:
        return False

def is_port_listening(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False

def restricted_input(prompt, allowed_pattern):
    def handle_sigint(signum, frame):
        print("\n\n")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_sigint)

    sys.stdout.write("\033[1;32m" + prompt + "\033[0m")
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)

    buffer = ""
    try:
        while True:
            r, _, _ = select.select([fd], [], [], 0)
            if r:
                ch = sys.stdin.read(1)
                if ch == "\n" or ch == "\r":
                    print()
                    break
                elif ch == "\x03":
                    raise KeyboardInterrupt
                elif ch == "\x7f":
                    if buffer:
                        buffer = buffer[:-1]
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                elif re.match(allowed_pattern, ch):
                    buffer += ch
                    sys.stdout.write(ch)
                    sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\n")
        sys.exit(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return buffer

def main():
    if os.geteuid() != 0:
        print_red("Please Use Root Environment.")
        sys.exit(1)

    if not is_installed("nginx -v"):
        print_green("Installing NGINX ...")
        run_command("sudo apt update -o Acquire::AllowInsecureRepositories=true")
        run_command("sudo apt install -y nginx")
        run_command("sudo systemctl start nginx")
        run_command("sudo systemctl enable nginx")
    else:
        print_green("NGINX installed.")

    if not is_installed("certbot --version"):
        print_green("Installing Certbot ...")
        run_command("sudo apt update -o Acquire::AllowInsecureRepositories=true")
        run_command("sudo apt install -y certbot python3-certbot-nginx")
    else:
        print_green("Certbot installed.")
        
    if not is_certbot_nginx_plugin_installed():
        print_green("Installing python3-certbot-nginx plugin ...")
        run_command("sudo apt update -o Acquire::AllowInsecureRepositories=true")
        run_command("sudo apt install -y python3-certbot-nginx")
    else:
        print_green("python3-certbot-nginx plugin installed.")
        print("\n")

    print_yellow("┌─╼ Enter Domain Or Subdomain")
    domain = restricted_input("\033[1;33m└────╼ ❯❯❯ \033[0m", r"[a-zA-Z0-9\.\-]")
    
    print("\n")
    
    if "." not in domain:
        print_red("Domain is invalid, Operation Failed.")
        sys.exit(1)

    print_yellow("┌─╼ Enter Port To Expose")
    port = restricted_input("\033[1;33m└────╼ ❯❯❯ \033[0m", r"[0-9]+")
    
    print("\n")

    if not is_port_listening(port):
        print_red("Port Not Listening, Operation Failed.")
        sys.exit(1)

    nginx_temp_conf = f"""
server {{
    server_name {domain};

    location /nitroverify/auth.txt {{
        default_type text/plain;
        return 200 "nitroverify-success";
    }}

    location / {{
        return 404;
    }}

    listen 80;
}}
"""
    conf_path = f"/etc/nginx/sites-available/{domain}"
    with open(conf_path, "w") as f:
        f.write(nginx_temp_conf)

    run_command(f"sudo ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")
    run_command("sudo systemctl reload nginx")

    print_yellow("Domain verifying...")
    time.sleep(5)

    verified = False
    for url in [f"http://{domain}/nitroverify/auth.txt", f"https://{domain}/nitroverify/auth.txt"]:
        try:
            r = requests.get(url, timeout=5)
            if "nitroverify-success" in r.text:
                verified = True
                break
        except Exception:
            continue

    if not verified:
        print_red("Domain Verification Failed, Check Records Carefully.")
        run_command(f"sudo rm -f /etc/nginx/sites-available/{domain}")
        run_command(f"sudo rm -f /etc/nginx/sites-enabled/{domain}")
        run_command("sudo systemctl reload nginx")
        sys.exit(1)

    print_green("Domain Verification Success.\n")

    run_command(f"sudo rm -f /etc/nginx/sites-available/{domain}")
    run_command(f"sudo rm -f /etc/nginx/sites-enabled/{domain}")
    run_command("sudo systemctl reload nginx")

    nginx_conf = f"""
server {{
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    listen 80;
}}
"""
    conf_path = f"/etc/nginx/sites-available/{domain}"
    with open(conf_path, "w") as f:
        f.write(nginx_conf)

    run_command(f"sudo ln -sf /etc/nginx/sites-available/{domain} /etc/nginx/sites-enabled/")
    run_command("sudo systemctl reload nginx")

    run_command(f"sudo certbot --nginx -d {domain} --non-interactive --agree-tos --email nitroexpose@gmail.com")
    run_command("sudo systemctl reload nginx")

    print_yellow("\nSSL Certificate Checking...")
    time.sleep(2)

    ssl_installed = False
    try:
        r = requests.get(f"https://{domain}", timeout=10)
        if r.status_code == 200:
            ssl_installed = True
    except requests.exceptions.SSLError:
        ssl_installed = False
    except requests.exceptions.RequestException:
        ssl_installed = False

    print("\n")
    if ssl_installed:
        print_green(f"Exposed Successfully To Domain\n")
        print_green(f"Exposed On: https://{domain}\n")
        print_green(f"Port: {port}\n")
        print_green(f"SSL Installed Using Let's Encrypt.\n\n")
    else:
        print_green(f"Exposed Successfully To Domain\n")
        print_green(f"Exposed On: http://{domain}\n")
        print_green(f"Port: {port}\n")
        print_yellow(f"Unfortunately, please verify your records carefully. Your server is exposed on your domain, and we are experiencing difficulties while attempting to install an SSL certificate.\n\n")

if __name__ == "__main__":
    main()