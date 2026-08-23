# SecureGuard-v5-pro
SecureGuard Pro v5.3 is a lightweight, privacy-focused EDR tool for ransomware detection, prevention, and response. It provides real-time file and process monitoring, multi-layer scanning, threat scoring, quarantine, backups, automated response, and JSON/HTML reporting for authorized security testing.
<img width="1232" height="267" alt="image" src="https://github.com/user-attachments/assets/45ec237b-1850-49ab-84fa-7e7e8852738a" />
Cli Interface
<img width="657" height="710" alt="image" src="https://github.com/user-attachments/assets/907879e4-6d24-4d27-873e-24cf5c61f977" />
<img width="657" height="710" alt="image" src="https://github.com/user-attachments/assets/b61de322-6da0-4d7a-a371-befcc3acf4e7" />
✨ Key Features & Capabilities
Custom CLI Banner & Boot Telemetry
Stylized ASCII interface and SecureGuard branding
Version and tool classification display
Automated scan mode selection
Configurable detection sensitivity profiles
Heuristic Ransomware Detection Engine
Recursively scans monitored directories
Identifies suspicious file activity and naming patterns
Uses path filtering to reduce unnecessary scanning
Extension Pattern Recognition
Detects suspicious ransomware-style extensions
Identifies patterns such as .locked.test
Detects suspicious double extensions
Quantified Threat Scoring
Assigns scores to detected suspicious files
Produces a normalized 0–100 threat score
Maps scores to risk levels such as LOW, MODERATE, HIGH, and CRITICAL
Automated Quarantine
Isolates detected suspicious files
Moves flagged files into a dedicated quarantine location
Helps prevent further interaction with suspicious files
Threat Reporting
Generates timestamped scan reports
Supports machine-readable JSON reporting
Supports CSV reporting for spreadsheet/data analysis
Maintains scan information for later review
Workspace Isolation
Separates application data from source code
Maintains dedicated locations for reports and quarantine data
Supports backup and recovery workflows
Python Virtual Environment Support
Runs in an isolated Python environment
Keeps project dependencies separate from system Python
Uses requirements.txt for dependency installation
