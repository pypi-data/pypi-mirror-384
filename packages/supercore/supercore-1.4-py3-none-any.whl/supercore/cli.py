import os
import subprocess
import sys
import random
import re
import termios
import tty
import select
import signal

# 𝗠𝗮𝗻𝗮𝗴𝗲𝗱 𝗕𝘆 @𝗡𝗮𝗰𝘁𝗶𝗿𝗲

def check_supervisor_installed():
    try:
        subprocess.run(
            ["supervisord", "-v"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[INFO] Supervisor installing...")
        subprocess.run(["sudo", "apt", "update", "-o", "Acquire::AllowInsecureRepositories=true"], check=True)
        subprocess.run(["sudo", "apt", "install", "supervisor", "-y"], check=True)

def detect_virtualenv_path():
    venv_path = os.environ.get("VIRTUAL_ENV")
    return venv_path if venv_path else None

def adjust_python_command(command):
    parts = command.strip().split()
    if not parts:
        return command
    first_word = parts[0]
    if first_word not in ["python", "python3"]:
        return command
    venv_path = detect_virtualenv_path()
    if venv_path:
        venv_python = os.path.join(venv_path, "bin", "python")
        parts[0] = venv_python
        command = " ".join(parts)
    return command

def _is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def get_filtered_input(prompt):
    sys.stdout.write("\033[1;33m" + prompt + "\033[0m")
    sys.stdout.flush()
    result = ""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    allowed_re = re.compile(r"[A-Za-z0-9-]")
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if not ch:
                continue
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                break
            if ch == "\x03":
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                raise KeyboardInterrupt
            if ch in ("\x7f", "\b"):
                if len(result) > 0:
                    result = result[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            if allowed_re.fullmatch(ch):
                result += ch
                sys.stdout.write(ch)
                sys.stdout.flush()
                continue
            sys.stdout.write(ch)
            sys.stdout.flush()
            sys.stdout.write("\b \b")
            sys.stdout.flush()
            continue
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return result

def get_custom_process_name():
    try:
        process_name = get_filtered_input("┌─╼ 𝗘𝗻𝘁𝗲𝗿 𝗣𝗿𝗼𝗰𝗲𝘀𝘀 𝗡𝗮𝗺𝗲\n└────╼ ❯❯❯ ")
    except KeyboardInterrupt:
        print("\n\033[1;31m𝗢𝗽𝗲𝗿𝗮𝘁𝗶𝗼𝗻 𝗖𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱 𝗕𝘆 𝗨𝘀𝗲𝗿.\033[0m")
        sys.exit(1)
    if not process_name:
        print("\033[1;31m𝗣𝗿𝗼𝗰𝗲𝘀𝘀 𝗡𝗮𝗺𝗲 𝗶𝘀 𝗶𝗻𝘃𝗮𝗹𝗶𝗱, 𝗧𝗿𝘆 𝗔𝗴𝗮𝗶𝗻.\n(𝗡𝗼 𝗦𝗽𝗮𝗰𝗲, 𝗡𝗼 𝗦𝗽𝗲𝗰𝗶𝗮𝗹 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿)\033[0m")
        sys.exit(1)
    if not re.fullmatch(r"[A-Za-z0-9-]+", process_name):
        print("\033[1;31m𝗣𝗿𝗼𝗰𝗲𝘀𝘀 𝗡𝗮𝗺𝗲 𝗶𝘀 𝗶𝗻𝘃𝗮𝗹𝗶𝗱, 𝗧𝗿𝘆 𝗔𝗴𝗮𝗶𝗻.\n(𝗡𝗼 𝗦𝗽𝗮𝗰𝗲, 𝗡𝗼 𝗦𝗽𝗲𝗰𝗶𝗮𝗹 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿)\033[0m")
        sys.exit(1)
    conf_path = f"/etc/supervisor/conf.d/{process_name}.conf"
    if os.path.exists(conf_path):
        print("\033[1;31m𝗣𝗿𝗼𝗰𝗲𝘀𝘀 𝗡𝗮𝗺𝗲 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗘𝘅𝗶𝘀𝘁𝘀,\n𝗧𝗿𝘆 𝗔𝗴𝗮𝗶𝗻 𝗪𝗶𝘁𝗵 𝗗𝗶𝗳𝗳𝗲𝗿𝗲𝗻𝘁 𝗡𝗮𝗺𝗲.\033[0m")
        sys.exit(1)
    return process_name

def create_supervisor_conf(command, process_name):
    current_dir = os.getcwd()
    conf_path = f"/etc/supervisor/conf.d/{process_name}.conf"
    conf_content = f"""[program:{process_name}]
directory={current_dir}
command={command}
autostart=true
autorestart=true
stderr_logfile=/var/log/{process_name}.err.log
stdout_logfile=/var/log/{process_name}.out.log
user=root
"""
    with open(f"/tmp/{process_name}.conf", "w") as f:
        f.write(conf_content)
    subprocess.run(["sudo", "mv", f"/tmp/{process_name}.conf", conf_path], check=True)
    return process_name

def start_supervisor_process(process_name):
    print("\n")
    subprocess.run(["sudo", "supervisorctl", "reread"], check=True)
    subprocess.run(["sudo", "supervisorctl", "update"], check=True)
    print(f"\033[1;92m"
          f"\nSupervisor Process Started Successfully!\n"
          f"Process Name: {process_name}\n\n"
          f"Quick Commands:\n"
          f"supervisorctl restart {process_name}\n"
          f"supervisorctl stop {process_name}\n"
          f"supervisorctl start {process_name}\n\n"
          f"Logs Trace Commands:\n"
          f"tail -f /var/log/{process_name}.out.log\n"
          f"tail -f /var/log/{process_name}.err.log\n\n"
          f"To Manage Config File:\n"
          f"nano /etc/supervisor/conf.d/{process_name}.conf\n"
          f"\033[0m")

def generate_random_code():
    return random.randint(1000, 9999)

def main():
    if len(sys.argv) < 2:
        print("\033[1;31m𝗦𝗽𝗲𝗰𝗶𝗳𝘆 𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗧𝗼 𝗦𝘁𝗮𝗿𝘁 𝗣𝗿𝗼𝗰𝗲𝘀𝘀.\033[0m")
        sys.exit(1)
    raw_command = " ".join(sys.argv[1:])
    check_supervisor_installed()
    adjusted_command = adjust_python_command(raw_command)
    process_name = get_custom_process_name()
    create_supervisor_conf(adjusted_command, process_name)
    start_supervisor_process(process_name)

if __name__ == "__main__":
    main()
