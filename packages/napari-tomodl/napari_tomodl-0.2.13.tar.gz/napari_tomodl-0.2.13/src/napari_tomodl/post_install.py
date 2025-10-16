import platform, subprocess, sys

def install_torch():
    system = platform.system()
    if system == "Windows":
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch==2.4.1", "--index-url", "https://download.pytorch.org/whl/cu124", "QBI-radon", "pyopengl==3.1.6"
        ]
    else:
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch==2.4.1", "--index-url", "https://download.pytorch.org/whl/cu124", "QBI-radon", "pyopengl==3.1.6"
        ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    install_torch()