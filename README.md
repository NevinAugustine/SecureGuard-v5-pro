# SecureGuard-v5-pro
SecureGuard Pro v5.3 is a lightweight, privacy-focused EDR tool for ransomware detection, prevention, and response. It provides real-time file and process monitoring, multi-layer scanning, threat scoring, quarantine, backups, automated response, and JSON/HTML reporting for authorized security testing.
<img width="1232" height="267" alt="image" src="https://github.com/user-attachments/assets/45ec237b-1850-49ab-84fa-7e7e8852738a" />
Cli Interface
<img width="496" height="776" alt="Screenshot 2026-08-23 225437" src="https://github.com/user-attachments/assets/854528fa-604e-4cd1-bebc-e24a5d985678" />


## 🛡️ Key Features

-  **Deep Scan** — Recursive file scanning with ransomware pattern detection.
-  **Ransomware Detection** — Detects suspicious extensions and file activity.
-  **Auto-Quarantine** — Isolates detected suspicious files.
-  **Persistence Detection** — Checks cron jobs, startup files, and shell profiles.
-  **Spyware Detection** — Identifies suspicious processes and surveillance activity.
-  **Threat Scoring** — Calculates and classifies overall security risk.
-  **Reporting** — Generates JSON and CSV security reports.
-  **Real-Time Monitoring** — Monitors suspicious system and file activity.
  
## 🚀 Usage

SecureGuard Pro is designed for authorized defensive security and endpoint monitoring.

### Where It Can Be Used

* 🖥️ **Linux Endpoints** — Monitor files, processes, and system activity.
* 🧪 **Security Labs** — Test ransomware and malware detection techniques in isolated environments.
* 🔬 **Malware Analysis** — Analyze suspicious file and process behavior.
* 🛡️ **Incident Response** — Identify and contain suspicious activity.
* 🎓 **Cybersecurity Learning** — Learn about EDR, ransomware detection, and endpoint security.

  
 ## 🧪 Safe Ransomware Simulator

SecureGuard includes an optional **harmless ransomware simulator** for educational and testing purposes. The simulator automatically creates its own designated test files with ransomware-like indicators so SecureGuard can detect and demonstrate its security capabilities.

The simulator does **not infect, encrypt, or modify real user files**. All generated files are intended only for controlled testing.

### Purpose

- Test ransomware detection
- Demonstrate threat scoring
- Test quarantine functionality
- Validate security alerts
- Demonstrate SecureGuard in a safe environment
- Support cybersecurity education and research

> ⚠️ **Educational Use Only:** The simulator is designed for controlled security testing and creates test files specifically for SecureGuard detection. Do not modify it to target real or unauthorized data.

### Run SecureGuard

```bash
source venv/bin/activate
python3 secureguard.py
```

Deactivate

⚠️ Use SecureGuard only on systems you own or have explicit authorization to monitor.








⚠️ Disclaimer


SecureGuard Pro is an educational and defensive cybersecurity tool intended for authorized security testing,security research, and endpoint protection.



