#!/usr/bin/env python3
"""
SecureGuard Pro v5.3 - Ransomware Directory Edition
========================================================================
All paths are now inside ~/ransomware/:
  - Quarantine: ~/ransomware/SecureGuard_Quarantine
  - Logs: ~/ransomware/SecureGuard_Logs
  - Backups: ~/ransomware/.secureguard_backups
  - Config: ~/ransomware/.secureguard

Usage:
  python3 secureguard.py               -> Automated full scan
  python3 secureguard.py -i            -> Interactive dashboard
"""

import os
import sys
import re
import time
import json
import math
import glob
import html
import hashlib
import shutil
import threading
import subprocess
from datetime import datetime
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ============================================================
# THIRD-PARTY IMPORTS (Graceful fallback)
# ============================================================

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ============================================================
# ANSI COLOR HELPERS
# ============================================================

class C:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    GRAY    = '\033[90m'
    DARK_BLUE = '\033[38;5;19m'  # Dark blue
    LIGHT_BLUE = '\033[38;5;33m' # Light blue

if os.name == "nt":
    try:
        os.system("")  # enable ANSI on Windows consoles
    except Exception:
        pass

try:
    _STDOUT_IS_TTY = sys.stdout.isatty()
except Exception:
    _STDOUT_IS_TTY = False

USE_COLORS = _STDOUT_IS_TTY and not os.environ.get("NO_COLOR")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def color(text: str, *codes: str) -> str:
    if not USE_COLORS:
        return text
    return "".join(codes) + text + C.RESET


def vis_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def c_ok(text):   return color(text, C.GREEN)
def c_warn(text): return color(text, C.YELLOW)
def c_err(text):  return color(text, C.RED)
def c_info(text): return color(text, C.CYAN)
def c_head(text): return color(text, C.MAGENTA, C.BOLD)
def c_acc(text):  return color(text, C.BLUE)
def c_dim(text):  return color(text, C.GRAY)


def section_header(title: str, ccode: str = C.MAGENTA):
    """Single-line colored section header."""
    print(f"\n{color('━━━', ccode, C.BOLD)} {c_head(title)} {color('━━━', ccode, C.BOLD)}")


def bbox_row(text: str, width: int) -> str:
    pad = max(0, width - 3 - vis_len(text))
    return "║ " + text + " " * pad + "║"


def make_box(title: str, rows: List[str], width: int = 62,
             tcolor: str = C.CYAN) -> str:
    """One full box with an optional colored title line."""
    W = max(width, 30)
    out = [color("╔" + "═" * (W - 2) + "╗", C.GRAY)]
    if title:
        out.append(bbox_row(color(f" {title} ", tcolor, C.BOLD), W))
        out.append(color("╠" + "═" * (W - 2) + "╣", C.GRAY))
    for r in rows:
        out.append(bbox_row(r, W))
    out.append(color("╚" + "═" * (W - 2) + "╝", C.GRAY))
    return "\n".join(out)


def threat_level(score: int) -> Tuple[str, str]:
    if score >= 70:
        return "HIGH", C.RED
    if score >= 30:
        return "MODERATE", C.YELLOW
    return "LOW", C.GREEN


def score_box(stats: dict, alert_count: int) -> str:
    """All scoring stats inside ONE full box."""
    score = stats["threat_score"]
    level, lc = threat_level(score)
    rows = [
        color("Threat Score       : ", C.WHITE) + color(f"{score}/100", lc, C.BOLD),
        color("Threat Level       : ", C.WHITE) + color(f"{level}", lc, C.BOLD),
        color("Threats Blocked    : ", C.WHITE) + color(str(stats["threats_blocked"]), C.YELLOW),
        color("Files Quarantined  : ", C.WHITE) + color(str(stats["files_quarantined"]), C.YELLOW),
        color("Backups Created    : ", C.WHITE) + color(str(stats["backups_created"]), C.YELLOW),
        color("Alerts Logged      : ", C.WHITE) + color(str(alert_count), C.YELLOW),
    ]
    return make_box("THREAT SCORE SUMMARY", rows)

# ============================================================
# PROFESSIONAL DARK BLUE BANNER DESIGN
# ============================================================

BANNER_ART = """\
███████╗███████╗ ██████╗██╗   ██╗██████╗ ███████╗ ██████╗██╗   ██╗ █████╗ ██████╗ ██████╗
██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝██╔════╝██║   ██║██╔══██╗██╔══██╗██╔══██╗
███████╗█████╗  ██║     ██║   ██║██████╔╝█████╗  ██║  ███╗██║   ██║███████║██████╔╝██║  ██║
╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
███████║███████╗╚██████╗╚██████╔╝██║  ██║███████╗╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝"""

# DARK BLUE PROFESSIONAL COLOR SCHEME
BANNER_COLORS = [
    C.BLUE,      # Line 1 - Primary blue
    C.DARK_BLUE, # Line 2 - Dark blue
    C.BLUE,      # Line 3 - Primary blue
    C.DARK_BLUE, # Line 4 - Dark blue
    C.BLUE,      # Line 5 - Primary blue
    C.CYAN       # Line 6 - Cyan accent
]


def print_banner(mode: str = "SECUREGUARD PRO v5.3"):
    """Professional dark blue SECUREGUARD banner."""
    art_lines = [l.rstrip() for l in BANNER_ART.split("\n")]

    info_lines = [
        ("SecureGuard Pro v5.3  •  Endpoint Detection & Response", C.WHITE, True),
        ("MODE: " + mode + "  •  PROFILE: " + config.active_profile.upper(), C.CYAN, False),
    ]

    # Calculate width
    inner_w = max(vis_len(l) for l in art_lines + [t for t, _, _ in info_lines])
    W = inner_w + 4

    out = [color("╔" + "═" * (W - 2) + "╗", C.DARK_BLUE)]

    # Art lines with dark blue professional colors
    for i, line in enumerate(art_lines):
        colored = color(line, C.BOLD, BANNER_COLORS[i % len(BANNER_COLORS)])
        pad = inner_w - vis_len(line)
        out.append("║ " + colored + " " * pad + " ║")

    out.append(color("╠" + "═" * (W - 2) + "╣", C.DARK_BLUE))

    # Info lines - clean and professional
    for text, col, bold in info_lines:
        colored = color(text, col, C.BOLD) if bold else color(text, col)
        total_pad = inner_w - vis_len(text)
        left = total_pad // 2
        right = total_pad - left
        out.append("║ " + " " * left + colored + " " * right + " ║")

    out.append(color("╚" + "═" * (W - 2) + "╝", C.DARK_BLUE))
    print("\n".join(out))

# ============================================================
# RANSOMWARE EXTENSIONS DATABASE
# ============================================================

RANSOMWARE_EXTENSIONS = {
    '.wncry', '.wcry', '.wncry!', '.wncry@', '.wncry2',
    '.lockbit', '.lockbit2', '.lockbit3', '.lockbit4',
    '.lockbit5', '.lockbit6', '.lockbit7', '.lockbit8',
    '.lockbit2023', '.lockbit2024',
    '.conti', '.conti2', '.conti3', '.conti4',
    '.blackcat', '.alphv', '.hive',
    '.basta', '.blackbasta',
    '.clop', '.cl0p', '.clipp', '.crypt',
    '.sodinokibi', '.revil', '.abcd', '.djvu', '.kukipp',
    '.maze', '.maze2', '.maze3', '.maze4',
    '.ryk', '.ryuk', '.r5k', '.ryuk2023', '.ryuk2024',
    '.dharma', '.crysis', '.wallet', '.bip',
    '.phobos', '.phobos2', '.phobos3', '.phobos4',
    '.zeppelin', '.zeppel', '.zeppelin2',
    '.avdn', '.avaddon', '.avaddon2',
    '.ragnar', '.ragnar2', '.ragnar3',
    '.globeimposter', '.globeimposter2', '.globe',
    '.deadbolt', '.deadbolt2', '.deadbolt3',
    '.akira', '.akira2', '.akira3',
    '.medusa', '.medusa2', '.medusa3',
    '.royal', '.royal2023',
    '.cryptolocker', '.cryptowall', '.cryptowall2', '.cryptowall3',
    '.cerber', '.cerber2', '.cerber3', '.cerber4', '.cerber5',
    '.locky', '.locky2', '.zepto', '.odin', '.thor', '.venus',
    '.ekans', '.payme', '.decrypt',
    '.npu', '.vault', '.kraken', '.satan', '.bitpay',
    '.blackheart', '.darkness', '.dede',
    '.petya', '.notpetya', '.badrabbit', '.xdata', '.x3m',
    '.crypted', '.encrypted', '.locked', '.crypt',
    '.enc', '.aes', '.rsa', '.onion',
    '.nightshade', '.quantum', '.vice', '.sugar', '.cuba',
    '.darkbyte', '.everest', '.hello', '.karakurt',
    '.lv', '.monte', '.nefilim', '.pysa', '.ranion',
    '.sova', '.sunset', '.victory', '.yashma',
    '.zorro', '.atom', '.biden', '.darkside',
    '.eb', '.fargo', '.gandcrab', '.hades', '.ice',
    '.jigsaw', '.lorenz', '.mamba',
    '.netwalker', '.orange', '.prometheus', '.qwerty',
    '.snatch', '.tampa', '.u2', '.vasta',
    '.xing', '.yam', '.zeus',
    '.locked.test',
}

RANSOM_NOTE_PATTERNS = [
    "readme", "how_to_decrypt", "recover_files",
    "decrypt_instructions", "restore_files", "your_files",
    "ransom", "payment", "read_me", "help_decrypt",
    "recovery", "instructions", "attention",
    "important", "warning", "all_files", "decrypt_guide",
    "files_encrypted", "decrypt_your_files", "recover_data",
    "how_to_return_files", "decrypt.txt", "recover.txt",
    "note.txt", "ransom_note", "!!!", "!!!_readme",
    "get_back_files", "return_files", "pay_ransom",
    "bitcoin", "monero", "wallet", "ransomware",
]

SUSPICIOUS_PROCESS_NAMES = [
    "wannacry", "lockbit", "conti", "blackcat", "alphv",
    "basta", "clop", "revil", "maze", "ryuk", "dharma",
    "phobos", "zeppelin", "avaddon", "ragnar", "akira",
    "medusa", "cryptolocker", "cerber", "locky", "petya",
    "ransomware", "encrypt", "decrypt", "ransom",
    "crypt", "crypto", "mimikatz", "cobaltstrike",
]

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def expand_path(path: str) -> str:
    return os.path.expanduser(os.path.expandvars(path))

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""

def compute_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for byte in data:
        freq[byte] += 1
    entropy = 0.0
    data_len = len(data)
    for count in freq:
        if count == 0:
            continue
        p = count / data_len
        entropy -= p * math.log2(p)
    return entropy

def get_file_entropy(filepath: str, sample_size: int = 8192) -> float:
    try:
        with open(filepath, 'rb') as f:
            data = f.read(sample_size)
        return compute_entropy(data)
    except Exception:
        return 0.0

def is_ransom_note(filename: str) -> bool:
    name_lower = filename.lower()
    for pattern in RANSOM_NOTE_PATTERNS:
        if pattern in name_lower:
            return True
    return False

def get_all_extensions(filepath: str) -> list:
    parts = os.path.basename(filepath).split('.')
    if len(parts) <= 1:
        return []
    return ['.' + p for p in parts[1:]]

def has_ransomware_extension(filepath: str) -> bool:
    all_exts = get_all_extensions(filepath)
    for ext in all_exts:
        if ext in RANSOMWARE_EXTENSIONS:
            return True
    return False

def is_naturally_high_entropy(filepath: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    all_exts = get_all_extensions(filepath)

    always_high = {
        '.zip', '.7z', '.rar', '.gz', '.gzip', '.lzma', '.bz2', '.xz', '.tar', '.tgz',
        '.br', '.brotli', '.lz4', '.lz4hc', '.zst', '.zstd',
        '.lz', '.lzo', '.lzh',
        '.001', '.002', '.003', '.004', '.005', '.006', '.007', '.008', '.009',
        '.r00', '.r01', '.r02', '.r03', '.r04', '.r05', '.r06', '.r07', '.r08', '.r09',
        '.part1', '.part2', '.part3',
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.ico', '.heic',
        '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.flac', '.wav', '.ogg', '.aac',
        '.webm', '.3gp', '.m4v', '.ts', '.mts', '.m2ts', '.vob', '.flv', '.swf',
        '.iso', '.img', '.vmdk', '.vdi', '.qcow2', '.vhd', '.dmg',
        '.exe', '.dll', '.so', '.dylib', '.msi', '.deb', '.rpm', '.apk',
        '.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp',
        '.pdf', '.epub', '.mobi',
        '.pyc', '.pyo', '.class', '.jar', '.war', '.ear', '.dex',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        '.sqlite', '.sqlite3', '.db', '.mdb',
        '.o', '.a', '.ko', '.lib', '.obj',
        '.elf', '.bin', '.dat', '.pak', '.sav',
        '.cpu', '.prof', '.pprof', '.trace', '.perf',
    }

    if ext in always_high:
        return True
    for e in all_exts:
        if e in always_high:
            return True
    return False

# ============================================================
# DETECTION PROFILES
# ============================================================

class DetectionProfile(Enum):
    LOW = "low"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    PARANOID = "paranoid"

@dataclass
class ProfileConfig:
    burst_threshold: int
    entropy_threshold: float
    process_score_threshold: int

PROFILES = {
    DetectionProfile.LOW: ProfileConfig(10, 7.8, 100),
    DetectionProfile.BALANCED: ProfileConfig(5, 7.5, 70),
    DetectionProfile.AGGRESSIVE: ProfileConfig(3, 7.2, 50),
    DetectionProfile.PARANOID: ProfileConfig(2, 7.0, 30),
}

# ============================================================
# CONFIGURATION - ALL PATHS INSIDE ~/ransomware/
# ============================================================

@dataclass
class EDRConfig:
    """Main configuration for SecureGuard - all paths in ~/ransomware/"""
    active_profile: str = "balanced"
    burst_threshold: int = 5
    time_window: int = 10
    entropy_threshold: float = 7.5
    auto_kill_enabled: bool = True
    auto_quarantine: bool = True
    real_time_backup: bool = True
    monitored_directories: List[str] = field(default_factory=lambda: [
        "~/Desktop", "~/Documents", "~/Downloads", "~/Pictures"
    ])
    trusted_processes: List[str] = field(default_factory=lambda: [
        "python", "python3", "bash", "sh", "systemd", "launchd",
        "chrome", "firefox", "safari", "edge"
    ])
    
    # ALL PATHS NOW INSIDE ~/ransomware/
    config_dir: str = "~/ransomware/.secureguard"
    quarantine_dir: str = "~/ransomware/SecureGuard_Quarantine"
    log_dir: str = "~/ransomware/SecureGuard_Logs"
    backup_dir: str = "~/ransomware/.secureguard_backups"

    def apply_profile(self, profile: DetectionProfile):
        c = PROFILES[profile]
        self.burst_threshold = c.burst_threshold
        self.entropy_threshold = c.entropy_threshold
        self.process_score_threshold = c.process_score_threshold
        self.active_profile = profile.value

    def to_dict(self) -> dict:
        return {
            "active_profile": self.active_profile,
            "burst_threshold": self.burst_threshold,
            "time_window": self.time_window,
            "entropy_threshold": self.entropy_threshold,
            "auto_kill_enabled": self.auto_kill_enabled,
            "auto_quarantine": self.auto_quarantine,
            "real_time_backup": self.real_time_backup,
            "monitored_directories": self.monitored_directories,
            "trusted_processes": self.trusted_processes,
            "config_dir": self.config_dir,
            "quarantine_dir": self.quarantine_dir,
            "log_dir": self.log_dir,
            "backup_dir": self.backup_dir,
        }

    def save(self):
        path = expand_path(f"{self.config_dir}/config.json")
        ensure_dir(os.path.dirname(path))
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls) -> 'EDRConfig':
        path = expand_path("~/ransomware/.secureguard/config.json")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                cfg = cls(**data)
                profile_name = data.get("active_profile", "balanced")
                for p in DetectionProfile:
                    if p.value == profile_name:
                        cfg.apply_profile(p)
                        break
                return cfg
            except Exception:
                pass
        return cls()

config = EDRConfig.load()

# ============================================================
# THREAD-SAFE STATE
# ============================================================

class ThreadSafeState:
    """Thread-safe global state management."""

    def __init__(self):
        self._lock = threading.RLock()
        self._score = 0
        self._blocked = 0
        self._quarantined = 0
        self._backups = 0
        self._monitoring = False
        self._alerts = deque(maxlen=200)

    @property
    def threat_score(self):
        with self._lock:
            return self._score

    def update_score(self, delta: int):
        with self._lock:
            self._score = max(0, min(100, self._score + delta))

    def set_score(self, value: int):
        with self._lock:
            self._score = max(0, min(100, value))

    def add_alert(self, alert: dict):
        with self._lock:
            self._alerts.append(alert)

    def get_alerts(self, count: int = 50):
        with self._lock:
            return list(self._alerts)[-count:]

    def get_stats(self):
        with self._lock:
            return {
                "threat_score": self._score,
                "threats_blocked": self._blocked,
                "files_quarantined": self._quarantined,
                "backups_created": self._backups,
                "monitoring_active": self._monitoring,
            }

    def increment_blocked(self):
        with self._lock:
            self._blocked += 1

    def increment_quarantined(self):
        with self._lock:
            self._quarantined += 1

    def increment_backups(self):
        with self._lock:
            self._backups += 1

    def set_monitoring(self, active: bool):
        with self._lock:
            self._monitoring = active

    @property
    def monitoring_active(self):
        with self._lock:
            return self._monitoring

state = ThreadSafeState()
scan_results: Dict[str, dict] = {}

# ============================================================
# QUARANTINE MANAGER
# ============================================================

class QuarantineManager:
    """Manages quarantined files with restore capability."""

    def __init__(self):
        self.dir = expand_path(config.quarantine_dir)
        ensure_dir(self.dir)

    def quarantine(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            return False
        try:
            filename = os.path.basename(filepath)
            dest = os.path.join(self.dir, f"{int(time.time())}_{filename}")
            shutil.copy2(filepath, dest)
            meta = {
                "original_path": filepath,
                "quarantine_time": datetime.now().isoformat(),
                "sha256": compute_sha256(filepath),
            }
            with open(dest + ".meta", 'w') as f:
                json.dump(meta, f)
            os.remove(filepath)
            state.increment_quarantined()
            return True
        except Exception:
            return False

    def list_all(self) -> List[dict]:
        items = []
        for f in os.listdir(self.dir):
            if f.endswith('.meta'):
                continue
            full_path = os.path.join(self.dir, f)
            items.append({"path": full_path, "filename": f})
        return sorted(items, key=lambda x: x['filename'], reverse=True)

    def restore(self, quarantine_path: str) -> bool:
        meta_path = quarantine_path + ".meta"
        if not os.path.exists(meta_path):
            return False
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            original = meta.get("original_path")
            if original:
                os.makedirs(os.path.dirname(original), exist_ok=True)
                shutil.copy2(quarantine_path, original)
                os.remove(quarantine_path)
                os.remove(meta_path)
                return True
        except Exception:
            pass
        return False

quarantine_manager = QuarantineManager()

# ============================================================
# BACKUP MANAGER
# ============================================================

class BackupManager:
    """Manages automatic file backups."""

    def __init__(self):
        self.dir = expand_path(config.backup_dir)
        ensure_dir(self.dir)
        self._last_backup = {}

    def create_backup(self, filepath: str) -> Optional[str]:
        if not config.real_time_backup or not os.path.exists(filepath):
            return None
        now = time.time()
        if filepath in self._last_backup and now - self._last_backup[filepath] < 5:
            return None
        try:
            filename = os.path.basename(filepath)
            backup_name = f"{int(now)}_{filename}.bak"
            backup_path = os.path.join(self.dir, backup_name)
            shutil.copy2(filepath, backup_path)
            self._last_backup[filepath] = now
            state.increment_backups()
            return backup_path
        except Exception:
            return None

    def list_backups(self) -> List[dict]:
        backups = []
        for f in os.listdir(self.dir):
            if f.endswith('.bak'):
                full_path = os.path.join(self.dir, f)
                backups.append({
                    "backup_path": full_path,
                    "filename": f,
                    "created": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
                })
        return sorted(backups, key=lambda x: x['created'], reverse=True)

    def restore(self, backup_path: str, original_path: str = None) -> bool:
        if not os.path.exists(backup_path):
            return False
        try:
            if not original_path:
                parts = os.path.basename(backup_path).split('_', 2)
                if len(parts) > 2:
                    original_path = os.path.join(expand_path("~"), parts[2].replace('.bak', ''))
            if original_path:
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.copy2(backup_path, original_path)
                return True
        except Exception:
            pass
        return False

backup_manager = BackupManager()

# ============================================================
# RANSOMWARE DETECTOR
# ============================================================

class RansomwareDetector:
    """Enhanced detection engine for real ransomware."""

    @property
    def entropy_threshold(self):
        return config.entropy_threshold

    def detect(self, filepath: str, process_name: str = None) -> dict:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        name_lower = filename.lower()

        result = {
            'is_ransomware': False,
            'confidence': 0,
            'reasons': [],
            'family': None,
            'action_needed': False,
            'severity': 'low'
        }

        if is_ransom_note(filename):
            result['is_ransomware'] = True
            result['confidence'] = 100
            result['reasons'].append('Ransom note file detected')
            result['family'] = 'RansomNote'
            result['severity'] = 'critical'
            result['action_needed'] = True
            return result

        if has_ransomware_extension(filepath):
            result['is_ransomware'] = True
            result['confidence'] = 100
            result['reasons'].append(f'Known ransomware extension in: {filepath}')
            result['family'] = self._identify_family(ext)
            result['severity'] = 'critical'
            result['action_needed'] = True
            return result

        pattern_result = self._check_patterns(filename, filepath)
        if pattern_result['matched']:
            result['is_ransomware'] = True
            result['confidence'] = max(result['confidence'], pattern_result['confidence'])
            result['reasons'].append(pattern_result['reason'])
            result['family'] = pattern_result.get('family', 'Unknown')
            result['severity'] = 'high'
            if pattern_result['confidence'] >= 80:
                result['action_needed'] = True
            return result

        if process_name and self._is_suspicious_process(process_name):
            result['is_ransomware'] = True
            result['confidence'] = 80
            result['reasons'].append(f'Suspicious process: {process_name}')
            result['family'] = 'SuspiciousProcess'
            result['severity'] = 'high'
            result['action_needed'] = True
            return result

        if not is_naturally_high_entropy(filepath):
            entropy = get_file_entropy(filepath)
            if entropy > self.entropy_threshold:
                parent_dir = os.path.dirname(filepath)
                if self._has_ransom_note_in_dir(parent_dir):
                    result['is_ransomware'] = True
                    result['confidence'] = 75
                    result['reasons'].append(f'High entropy ({entropy:.2f}) with ransom note')
                    result['severity'] = 'medium'
                    result['action_needed'] = True

        if not ext:
            parent_dir = os.path.dirname(filepath)
            if self._has_ransom_note_in_dir(parent_dir):
                result['is_ransomware'] = True
                result['confidence'] = 70
                result['reasons'].append('File with no extension in ransom note directory')
                result['severity'] = 'medium'
                result['action_needed'] = True

        return result

    def _identify_family(self, ext: str) -> str:
        family_map = {
            '.wncry': 'WannaCry', '.wcry': 'WannaCry',
            '.lockbit': 'LockBit', '.lockbit2': 'LockBit',
            '.conti': 'Conti',
            '.blackcat': 'BlackCat', '.alphv': 'BlackCat',
            '.basta': 'BlackBasta',
            '.clop': 'Clop',
            '.sodinokibi': 'REvil', '.abcd': 'REvil',
            '.maze': 'Maze',
            '.ryk': 'Ryuk', '.ryuk': 'Ryuk',
            '.dharma': 'Dharma', '.crysis': 'Dharma',
            '.phobos': 'Phobos',
            '.zeppelin': 'Zeppelin',
            '.avdn': 'Avaddon',
            '.ragnar': 'RagnarLocker',
            '.deadbolt': 'DeadBolt',
            '.akira': 'Akira',
            '.medusa': 'Medusa',
            '.royal': 'Royal',
            '.encrypted': 'GenericEncrypted',
            '.locked': 'GenericLocked',
        }
        for key, family in family_map.items():
            if ext.startswith(key) or ext == key:
                return family
            if key in ext:
                return family
        return 'Unknown'

    def _check_patterns(self, filename: str, filepath: str) -> dict:
        result = {'matched': False, 'reason': '', 'confidence': 0, 'family': None}
        name_lower = filename.lower()

        if '.id-' in name_lower and '.dharma' in name_lower:
            result['matched'] = True
            result['reason'] = 'Dharma/CrySiS ransomware pattern'
            result['confidence'] = 95
            result['family'] = 'Dharma'
            return result

        if '.id-' in name_lower and '.phobos' in name_lower:
            result['matched'] = True
            result['reason'] = 'Phobos ransomware pattern'
            result['confidence'] = 95
            result['family'] = 'Phobos'
            return result

        if '@' in name_lower and '.' in name_lower:
            parts = name_lower.split('.')
            if len(parts) >= 3 and any('@' in part for part in parts):
                result['matched'] = True
                result['reason'] = 'Ransomware with email in extension'
                result['confidence'] = 85
                result['family'] = 'EmailPattern'
                return result

        parts = filename.split('.')
        if len(parts) >= 3:
            last_ext = parts[-1].lower()
            if last_ext in ['exe', 'vbs', 'js', 'ps1', 'scr', 'com', 'cmd', 'bat', 'jar']:
                result['matched'] = True
                result['reason'] = 'Double extension malware pattern'
                result['confidence'] = 80
                result['family'] = 'DoubleExtension'
                return result

        ext = os.path.splitext(filename)[1].lower()
        if ext and len(ext) >= 3 and len(ext) <= 8:
            ext_clean = ext[1:]
            if ext_clean.isalnum() and ext_clean not in ['exe', 'dll', 'so']:
                parent_dir = os.path.dirname(filepath)
                if self._has_ransom_note_in_dir(parent_dir):
                    result['matched'] = True
                    result['reason'] = f'Random ransomware extension: {ext}'
                    result['confidence'] = 75
                    result['family'] = 'RandomExtension'
                    return result

        return result

    def _is_suspicious_process(self, process_name: str) -> bool:
        name_lower = process_name.lower()
        for sus_name in SUSPICIOUS_PROCESS_NAMES:
            if sus_name in name_lower:
                return True
        return False

    def _has_ransom_note_in_dir(self, directory: str) -> bool:
        try:
            if not os.path.exists(directory):
                return False
            for f in os.listdir(directory):
                if is_ransom_note(f):
                    return True
        except Exception:
            pass
        return False

detector = RansomwareDetector()

# ============================================================
# PROCESS UTILITIES
# ============================================================

def find_process_writing_file(filepath: str):
    if not PSUTIL_AVAILABLE:
        return None
    abs_path = os.path.abspath(filepath)
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            for f in proc.open_files():
                if f.path == abs_path and 'w' in f.mode:
                    return proc
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except Exception:
            continue
    return None

def kill_process_safely(process) -> bool:
    if not config.auto_kill_enabled:
        return False
    try:
        name = process.name()
        proc_base = os.path.splitext(os.path.basename(name))[0].lower()
        trusted_set = set(t.lower() for t in config.trusted_processes)
        if proc_base in trusted_set:
            return False
        for child in process.children(recursive=True):
            try:
                child.terminate()
            except Exception:
                pass
        process.terminate()
        try:
            process.wait(timeout=3)
        except Exception:
            process.kill()
        state.increment_blocked()
        return True
    except Exception:
        return False

# ============================================================
# REAL-TIME FILE MONITOR
# ============================================================

if WATCHDOG_AVAILABLE:
    class EDRFileMonitor(FileSystemEventHandler):
        """Real-time file system monitor with enhanced detection."""

        def __init__(self):
            super().__init__()
            self._lock = threading.RLock()
            self.history = defaultdict(list)
            self.last_alert = 0

        def on_modified(self, event):
            if not event.is_directory:
                self._handle(event.src_path)

        def on_created(self, event):
            if not event.is_directory:
                self._handle(event.src_path)

        def on_moved(self, event):
            if not event.is_directory:
                self._handle(event.dest_path)

        def _handle(self, path: str):
            now = time.time()

            process = None
            if PSUTIL_AVAILABLE:
                proc = find_process_writing_file(path)
                if proc:
                    process = proc.name()

            result = detector.detect(path, process)

            if result['is_ransomware']:
                with self._lock:
                    self.history["suspicious"].append({
                        "time": now,
                        "confidence": result['confidence'],
                        "family": result['family']
                    })
                    self.history["suspicious"] = [
                        e for e in self.history["suspicious"]
                        if now - e["time"] <= config.time_window
                    ]

                    if result['confidence'] >= 80:
                        self._alert("RANSOMWARE_DETECTED", path, result)
                        if config.auto_quarantine:
                            quarantine_manager.quarantine(path)
                        if process and config.auto_kill_enabled:
                            proc = find_process_writing_file(path)
                            if proc:
                                kill_process_safely(proc)

                    if len(self.history["suspicious"]) >= config.burst_threshold:
                        if now - self.last_alert >= 3:
                            self.last_alert = now
                            self._alert("ENCRYPTION_BURST", path, result)
                            if process and config.auto_kill_enabled:
                                proc = find_process_writing_file(path)
                                if proc:
                                    kill_process_safely(proc)

        def _alert(self, alert_type: str, path: str, result: dict):
            alert = {
                "type": alert_type,
                "file": path,
                "timestamp": datetime.now().isoformat(),
                "confidence": result.get('confidence', 0),
                "family": result.get('family', 'Unknown'),
                "reasons": result.get('reasons', [])
            }
            state.add_alert(alert)
            state.update_score(min(result.get('confidence', 50) // 10, 10))

            print(f"\n{color('🚨 ' + alert_type, C.RED, C.BOLD)}")
            print(f"   {c_info('File:')} {os.path.basename(path)}")
            print(f"   {c_info('Confidence:')} {c_warn(str(result.get('confidence', 0)) + '%')}")
            print(f"   {c_info('Family:')} {c_acc(str(result.get('family', 'Unknown')))}")
            print(f"   {c_info('Reason:')} {c_err(str(result.get('reasons', ['Unknown'])[0]))}")

# ============================================================
# MONITORING DAEMON
# ============================================================

class MonitoringDaemon:
    """Background monitoring daemon for real-time protection."""

    def __init__(self):
        self.observer = None
        self.running = False

    def start(self) -> bool:
        if not WATCHDOG_AVAILABLE:
            print(c_err("❌ watchdog required for real-time monitoring"))
            print(c_info("   Install: pip install watchdog"))
            return False
        if self.running:
            print(c_warn("⚠ Monitoring is already active"))
            return True

        dirs = [expand_path(d) for d in config.monitored_directories if os.path.exists(expand_path(d))]
        if not dirs:
            print(c_err("❌ No directories to monitor"))
            return False

        self.observer = Observer()
        handler = EDRFileMonitor()
        for d in dirs:
            self.observer.schedule(handler, d, recursive=True)

        self.observer.start()
        self.running = True
        state.set_monitoring(True)

        rows = [
            color("Profile     : ", C.WHITE) + c_acc(config.active_profile.upper()),
            color("Directories : ", C.WHITE) + c_info(str(len(dirs))),
            color("Threshold   : ", C.WHITE) + c_info(f"{config.burst_threshold} files/{config.time_window}s"),
            color("Auto-kill   : ", C.WHITE) + (c_ok("Enabled") if config.auto_kill_enabled else c_err("Disabled")),
        ]
        print()
        print(make_box("REAL-TIME PROTECTION ACTIVE", rows, tcolor=C.GREEN))
        return True

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.running = False
        state.set_monitoring(False)
        print(c_warn("🛑 Monitoring stopped"))

daemon = MonitoringDaemon()

# ============================================================
# SCANNERS - FIXED WITH LINEAR SCORING
# ============================================================

def quick_scan():
    """Quick ransomware scan."""
    section_header("QUICK RANSOMWARE SCAN")

    quick_data = {"suspicious_processes": [], "encrypted_files_in_monitored": []}

    if PSUTIL_AVAILABLE:
        print(c_info("\n📋 Checking running processes..."))
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                if any(s in name for s in SUSPICIOUS_PROCESS_NAMES):
                    print(f"  {c_warn('⚠')} Suspicious process: {c_warn(proc.info['name'])} (PID: {proc.info['pid']})")
                    quick_data["suspicious_processes"].append({
                        "name": proc.info['name'], "pid": proc.info['pid']
                    })
                    found = True
            except Exception:
                continue
        if not found:
            print(c_ok("  ✅ No suspicious processes detected"))
    else:
        print(c_warn("\n⚠ Process scanning disabled (psutil not installed)"))

    print(c_info("\n📁 Checking for encrypted files..."))
    encrypted = 0
    for d in config.monitored_directories:
        dir_path = expand_path(d)
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                full_path = os.path.join(dir_path, f)
                if has_ransomware_extension(full_path):
                    print(f"  {c_warn('⚠')} Encrypted file: {c_warn(full_path)}")
                    quick_data["encrypted_files_in_monitored"].append(full_path)
                    encrypted += 1

    if encrypted == 0:
        print(c_ok("  ✅ No encrypted files found"))
    else:
        state.update_score(encrypted * 5)

    print(c_info("\n📊 Threat Score: ") + c_warn(f"{state.threat_score}/100"))
    print(c_ok("✅ Quick scan complete"))
    scan_results["quick_scan"] = quick_data


def run_deep_scan(auto_quarantine: bool = True):
    """Deep ransomware scan with LINEAR scoring (1 point per file)."""
    section_header("DEEP RANSOMWARE SCAN")
    print(c_info("\nScanning entire home directory..."))
    print(c_dim("(Skipping known compressed/binary/media files)\n"))

    home = expand_path("~")
    encrypted_files = []
    skipped = 0
    scanned = 0

    skip_dirs = {
        '.git', '.svn', '.hg',
        'node_modules', '.npm',
        '__pycache__', 'venv', 'env', '.venv', '.env', 'envs', 'virtualenv',
        'go',
        '.cargo', '.rustup',
        '.m2', '.gradle', '.ivy', '.sbt',
        '.gem', '.bundle', 'vendor/bundle',
        'packages', 'bin', 'obj',
        '.cache', '.mozilla', '.npm', '.config/google-chrome',
        '.config/chromium', '.config/slack', '.config/discord',
        'snap', '.snap', '.local/share/flatpak',
        '.vscode', '.idea',
        # Skip our own directories inside ~/ransomware/
        'ransomware/SecureGuard_Quarantine',
        'ransomware/SecureGuard_Logs',
        'ransomware/.secureguard',
        'ransomware/.secureguard_backups',
        'SecureGuard_Quarantine', 'SecureGuard_Logs',
        '.secureguard', '.secureguard_backups',
        'testdata', 'test_data', 'fixtures', 'mockdata',
        'vendor', 'third_party', 'thirdparty',
        'site-packages', 'dist-packages',
    }

    try:
        for root, dirs, files in os.walk(home):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in skip_dirs]

            for file in files:
                filepath = os.path.join(root, file)

                if has_ransomware_extension(filepath):
                    encrypted_files.append(filepath)
                    if len(encrypted_files) <= 10:
                        print(f"  {c_warn('⚠ [Ransomware extension]')} {c_warn(filepath)}")

                elif not is_naturally_high_entropy(filepath):
                    try:
                        size = os.path.getsize(filepath)
                        if 100 <= size <= 50 * 1024 * 1024:
                            entropy = get_file_entropy(filepath)
                            if entropy > config.entropy_threshold:
                                encrypted_files.append(filepath)
                                if len(encrypted_files) <= 10:
                                    print(f"  {c_warn('⚠ [High entropy: %.2f]' % entropy)} {c_warn(filepath)}")
                    except Exception:
                        pass
                else:
                    skipped += 1

                scanned += 1
                if scanned % 1000 == 0:
                    print(f"  {c_dim('Progress:')} {scanned} files | Skipped: {skipped} | Threats: {len(encrypted_files)}")
    except PermissionError:
        print(c_warn("  ⚠ Permission error scanning some directories (skipping)"))

    print()
    section_header("DEEP SCAN RESULTS")
    
    # LINEAR SCORING: 1 point per suspicious file (max 100)
    suspicious_count = len(encrypted_files)
    
    if suspicious_count > 0:
        new_score = min(suspicious_count, 100)
        state.set_score(new_score)
        print(c_info(f"\n📊 SCORING: {suspicious_count} suspicious files → {new_score}/100 points (1 point per file)"))
    else:
        state.set_score(0)
    
    rows = [
        color("Total files scanned   : ", C.WHITE) + c_info(str(scanned)),
        color("Skipped (safe types)  : ", C.WHITE) + c_info(str(skipped)),
        color("Suspicious files      : ", C.WHITE) + (c_err(str(suspicious_count)) if suspicious_count else c_ok("0")),
        color("Threat Score          : ", C.WHITE) + c_warn(f"{state.threat_score}/100"),
    ]
    print(make_box("DEEP SCAN RESULTS", rows, tcolor=C.CYAN))

    quarantined = 0
    if encrypted_files:
        print(c_warn(f"\n⚠ {suspicious_count} suspicious files found:"))
        for f in encrypted_files[:10]:
            print(f"  • {c_warn(f)}")
        if suspicious_count > 10:
            print(c_dim(f"  ... and {suspicious_count - 10} more"))

        if auto_quarantine:
            print(c_info("\n🔒 Auto-quarantining suspicious files..."))
            for f in encrypted_files:
                if quarantine_manager.quarantine(f):
                    quarantined += 1
            print(c_ok(f"✅ {quarantined} files moved to quarantine"))
    else:
        print(c_ok("\n✅ NO RANSOMWARE INDICATORS FOUND"))

    scan_results["deep_scan"] = {
        "files_scanned": scanned,
        "skipped": skipped,
        "suspicious_files": encrypted_files,
        "quarantined": quarantined,
    }


def persistence_scan():
    """Scan for persistence mechanisms."""
    section_header("PERSISTENCE DETECTION")

    p_data = {"crontab_entries": [], "autostart_entries": [], "suspicious_shell_lines": {}}

    print(c_info("\n📋 Checking crontab..."))
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print(c_warn("  Crontab entries:"))
            for line in result.stdout.splitlines():
                if line.strip() and not line.strip().startswith('#'):
                    print(f"    • {c_warn(line.strip())}")
                    p_data["crontab_entries"].append(line.strip())
        else:
            print(c_ok("  ✅ No crontab entries"))
    except Exception:
        print(c_ok("  ✅ No crontab configured"))

    autostart = expand_path("~/.config/autostart")
    if os.path.exists(autostart):
        files = os.listdir(autostart)
        if files:
            print(c_warn(f"\n📁 Autostart entries ({len(files)}):"))
            for f in files:
                print(f"    • {c_warn(f)}")
                p_data["autostart_entries"].append(f)

    print(c_info("\n📋 Checking shell profiles for persistence hooks..."))
    profiles = [".bashrc", ".zshrc", ".profile", ".bash_profile"]
    found = False
    for profile in profiles:
        prof_path = expand_path(f"~/{profile}")
        if os.path.exists(prof_path):
            try:
                with open(prof_path, 'r') as f:
                    lines = f.readlines()
                suspicious = []
                for line in lines:
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        continue
                    lower = stripped.lower()
                    if any(p in lower for p in [
                        '/dev/tcp/', '/dev/udp/', 'nc -e', 'ncat -e',
                        'bash -i >&', '0<&196;exec 196<>/dev/tcp',
                        'exec 5<>/dev/tcp', 'mkfifo', 'mknod',
                        'eval "$(curl -s', 'eval "$(wget -q',
                        'source <(curl -s', 'source <(wget -q',
                        'strace -o', 'script -q', 'logkeys',
                        'alias sudo=', 'alias su=',
                    ]):
                        suspicious.append(stripped)
                if suspicious:
                    print(c_warn(f"  ⚠ {profile}: {len(suspicious)} suspicious line(s)"))
                    for line in suspicious[:3]:
                        print(f"    • {c_warn(line[:100])}")
                    p_data["suspicious_shell_lines"][profile] = suspicious
                    found = True
            except Exception:
                pass

    if not found:
        print(c_ok("  ✅ Shell profiles look clean"))

    print(c_ok("\n✅ Persistence scan complete"))
    scan_results["persistence_scan"] = p_data


def spyware_scan():
    """Scan for spyware, keyloggers, webcam and microphone access."""
    section_header("SPYWARE & PRIVACY SCANNER")

    if not PSUTIL_AVAILABLE:
        print(c_err("\n❌ psutil required for process scanning"))
        return

    threats = 0
    s_data = {"spyware": [], "webcam": [], "microphone": []}

    print(c_info("\n🔍 Checking for spyware/keyloggers..."))
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = (proc.info['name'] or "").lower()
            cmdline = " ".join(proc.info['cmdline'] or []).lower()
            for spy in ['keylogger', 'keylog', 'spyware', 'keyhook', 'clipmon']:
                if spy in name or spy in cmdline:
                    print(f"  {c_warn('⚠')} {c_warn(proc.info['name'])} (PID: {proc.info['pid']})")
                    s_data["spyware"].append({"name": proc.info['name'], "pid": proc.info['pid']})
                    threats += 1
                    break
        except Exception:
            continue
    if threats == 0:
        print(c_ok("  ✅ No spyware detected"))

    print(c_info("\n📷 Checking webcam access..."))
    webcam_found = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = (proc.info['name'] or "").lower()
            if any(x in name for x in ['camera', 'webcam', 'droidcam', 'cheese', 'guvcview']):
                print(f"  {c_warn('⚠')} Webcam: {c_warn(proc.info['name'])} (PID: {proc.info['pid']})")
                s_data["webcam"].append({"name": proc.info['name'], "pid": proc.info['pid']})
                webcam_found = True
                threats += 1
                break
        except Exception:
            continue
    if not webcam_found:
        print(c_ok("  ✅ No webcam access detected"))

    print(c_info("\n🎤 Checking microphone access..."))
    mic_found = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = (proc.info['name'] or "").lower()
            if any(x in name for x in ['microphone', 'mic', 'audio recorder', 'voice']):
                print(f"  {c_warn('⚠')} Microphone: {c_warn(proc.info['name'])} (PID: {proc.info['pid']})")
                s_data["microphone"].append({"name": proc.info['name'], "pid": proc.info['pid']})
                mic_found = True
                threats += 1
                break
        except Exception:
            continue
    if not mic_found:
        print(c_ok("  ✅ No microphone access detected"))

    if threats > 0:
        state.update_score(threats * 8)
        print(c_warn(f"\n⚠ {threats} privacy threat(s) found"))
    else:
        print(c_ok("\n✅ No privacy threats detected"))

    print(c_info(f"📊 Threat Score: ") + c_warn(f"{state.threat_score}/100"))
    scan_results["spyware_scan"] = s_data

# ============================================================
# REPORT WRITER
# ============================================================

def build_html_report(report: dict) -> str:
    """Build a self-contained dark-theme HTML report."""
    stats = report["stats"]
    score = stats["threat_score"]
    level, _ = threat_level(score)
    bar_color = "#f85149" if score >= 70 else ("#d29922" if score >= 30 else "#3fb950")

    def esc(v):
        return html.escape(str(v))

    alerts_rows = ""
    for a in report.get("alerts", []):
        alerts_rows += (
            "<tr>"
            f"<td>{esc(a.get('type'))}</td>"
            f"<td>{esc(os.path.basename(a.get('file', '')))}</td>"
            f"<td>{esc(a.get('family'))}</td>"
            f"<td>{esc(a.get('confidence'))}%</td>"
            f"<td>{esc(a.get('timestamp'))}</td>"
            "</tr>"
        )
    if not alerts_rows:
        alerts_rows = "<tr><td colspan='5' class='ok'>No alerts recorded</td></tr>"

    scans_html = ""
    for name, data in report.get("scans", {}).items():
        title = name.replace("_", " ").title()
        body = "<table class='kv'>"
        for key, val in data.items():
            if isinstance(val, list):
                items = "".join(
                    f"<li>{esc(i) if isinstance(i, str) else esc(i.get('name', i))}</li>"
                    for i in val[:10]
                ) or "<li>None</li>"
                body += f"<tr><td>{esc(key.replace('_', ' ').title())}</td><td><ul>{items}</ul></td></tr>"
            else:
                body += f"<tr><td>{esc(key.replace('_', ' ').title())}</td><td>{esc(val)}</td></tr>"
        body += "</table>"
        scans_html += f"<div class='panel'><h2>🔍 {esc(title)}</h2>{body}</div>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SecureGuard Pro Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Arial, sans-serif; padding: 24px; }}
  .top {{ background: linear-gradient(135deg, #f85149, #d29922, #3fb950, #58a6ff, #bc8cff);
         -webkit-background-clip: text; background-clip: text; color: transparent;
         font-size: 34px; font-weight: 800; text-align: center; letter-spacing: 2px; }}
  .sub {{ text-align: center; color: #8b949e; margin: 6px 0 22px; }}
  .cards {{ display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 22px; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 16px 20px; min-width: 160px; flex: 1; }}
  .card .label {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
  .card .value {{ font-size: 26px; font-weight: 700; margin-top: 6px; }}
  .scorebar-bg {{ background: #21262d; border-radius: 8px; height: 18px; margin: 10px 0 26px; overflow: hidden; }}
  .scorebar-fill {{ height: 100%; width: {score}%; background: {bar_color}; border-radius: 8px; transition: width 0.5s; }}
  .panel {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px; margin-bottom: 18px; }}
  h2 {{ color: #58a6ff; font-size: 18px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  .kv td {{ padding: 6px 10px; border-bottom: 1px solid #21262d; vertical-align: top; }}
  .kv td:first-child {{ color: #8b949e; width: 220px; }}
  th, td {{ text-align: left; }}
  th {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
  td, th {{ padding: 8px 10px; border-bottom: 1px solid #21262d; }}
  .ok {{ color: #3fb950; }} .warn {{ color: #d29922; }} .bad {{ color: #f85149; }}
  ul {{ margin-left: 18px; }} li {{ margin: 2px 0; }}
  .foot {{ text-align: center; color: #484f58; font-size: 12px; margin-top: 24px; }}
</style>
</head>
<body>
  <div class="top">SECUREGUARD PRO v5.3</div>
  <div class="sub">Endpoint Detection &amp; Response • Scan on {esc(report['timestamp'])} • Profile: {esc(report['profile'])}</div>

  <div class="cards">
    <div class="card"><div class="label">Threat Score</div><div class="value">{score}/100</div></div>
    <div class="card"><div class="label">Threat Level</div><div class="value" style="color:{bar_color}">{level}</div></div>
    <div class="card"><div class="label">Threats Blocked</div><div class="value">{stats['threats_blocked']}</div></div>
    <div class="card"><div class="label">Quarantined</div><div class="value">{stats['files_quarantined']}</div></div>
    <div class="card"><div class="label">Backups</div><div class="value">{stats['backups_created']}</div></div>
    <div class="card"><div class="label">Alerts</div><div class="value">{len(report.get('alerts', []))}</div></div>
  </div>

  <div class="scorebar-bg"><div class="scorebar-fill"></div></div>

  {scans_html}

  <div class="panel">
    <h2>🚨 Alert Log</h2>
    <table>
      <tr><th>Type</th><th>File</th><th>Family</th><th>Confidence</th><th>Timestamp</th></tr>
      {alerts_rows}
    </table>
  </div>

  <div class="foot">Generated by SecureGuard Pro v5.3 — ransomware detection for authorized security testing.</div>
</body>
</html>"""


def write_reports(stats: dict) -> Tuple[str, str]:
    """Write JSON and HTML reports to the log directory."""
    log_dir = expand_path(config.log_dir)
    ensure_dir(log_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    score = stats["threat_score"]
    level, _ = threat_level(score)

    report = {
        "tool": "SecureGuard Pro v5.3",
        "timestamp": datetime.now().isoformat(),
        "profile": config.active_profile,
        "threat_level": level,
        "stats": stats,
        "scans": scan_results,
        "alerts": state.get_alerts(50),
    }

    json_path = os.path.join(log_dir, f"secureguard_report_{ts}.json")
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)

    html_path = os.path.join(log_dir, f"secureguard_report_{ts}.html")
    with open(html_path, 'w') as f:
        f.write(build_html_report(report))

    print(c_ok(f"  📄 JSON report : {json_path}"))
    print(c_ok(f"  🌐 HTML report : {html_path}"))
    return json_path, html_path

# ============================================================
# DASHBOARD & MENU
# ============================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def menu():
    """Main interactive dashboard."""
    while True:
        clear_screen()
        print_banner(mode="INTERACTIVE DASHBOARD")
        stats = state.get_stats()
        score = stats['threat_score']
        _, lc = threat_level(score)

        rows = [
            color("Monitoring  : ", C.WHITE) + (c_ok("🟢 ACTIVE") if daemon.running else c_warn("⚪ STOPPED")),
            color("Profile     : ", C.WHITE) + c_acc(config.active_profile.upper()),
            color("Score       : ", C.WHITE) + color(f"{score}/100", lc, C.BOLD),
            color("Blocked     : ", C.WHITE) + c_warn(str(stats['threats_blocked'])) +
            color("   Quarantined: ", C.WHITE) + c_warn(str(stats['files_quarantined'])),
            color("Backups     : ", C.WHITE) + c_warn(str(stats['backups_created'])) +
            color("   Alerts      : ", C.WHITE) + c_warn(str(len(state.get_alerts()))),
        ]
        print(make_box("SECUREGUARD DASHBOARD", rows, tcolor=C.CYAN))

        menu_rows = [
            "[1] Start Monitor      [2] Stop Monitor",
            "[3] Quick Scan         [4] Deep Scan",
            "[5] Persistence        [6] Spyware Scan",
            "[7] Quarantine         [8] Backups",
            "[9] Restore Backup     [10] Switch Profile",
            "[11] Simulation        [0] Exit",
        ]
        print(make_box("MENU", menu_rows, tcolor=C.MAGENTA))

        choice = input("👉 Select option: ").strip()

        if choice == "1":
            daemon.start()
            input("\nPress Enter to continue...")
        elif choice == "2":
            daemon.stop()
            input("\nPress Enter to continue...")
        elif choice == "3":
            quick_scan()
            input("\nPress Enter to continue...")
        elif choice == "4":
            run_deep_scan(auto_quarantine=False)
            input("\nPress Enter to continue...")
        elif choice == "5":
            persistence_scan()
            input("\nPress Enter to continue...")
        elif choice == "6":
            spyware_scan()
            input("\nPress Enter to continue...")
        elif choice == "7":
            clear_screen()
            section_header("QUARANTINED FILES")
            items = quarantine_manager.list_all()
            if items:
                print(f"\n{c_info(str(len(items)))} quarantined file(s):\n")
                for i, item in enumerate(items[:20], 1):
                    print(f"  [{c_acc(str(i))}] {c_warn(item['filename'])}")
            else:
                print(c_ok("\n✅ Quarantine is empty"))
            input("\nPress Enter to continue...")
        elif choice == "8":
            clear_screen()
            section_header("BACKUPS")
            backups = backup_manager.list_backups()
            if backups:
                print(f"\n{c_info(str(len(backups)))} backup(s):\n")
                for i, b in enumerate(backups[:20], 1):
                    print(f"  [{c_acc(str(i))}] {c_warn(b['filename'])}")
            else:
                print(c_warn("\n📭 No backups created yet"))
            input("\nPress Enter to continue...")
        elif choice == "9":
            clear_screen()
            section_header("RESTORE FROM BACKUP")
            backups = backup_manager.list_backups()
            if backups:
                for i, b in enumerate(backups[:20], 1):
                    print(f"  [{c_acc(str(i))}] {c_warn(b['filename'])}")
                q = input("\nSelect backup number (0=cancel): ").strip()
                if q.isdigit() and 0 < int(q) <= len(backups):
                    original = input("Restore to path (Enter for original): ").strip()
                    if backup_manager.restore(backups[int(q) - 1]['backup_path'], original or None):
                        print(c_ok("✅ File restored successfully"))
                    else:
                        print(c_err("❌ Restore failed"))
            else:
                print(c_warn("\n📭 No backups available"))
            input("\nPress Enter to continue...")
        elif choice == "10":
            clear_screen()
            section_header("DETECTION PROFILE")
            print(f"\n{c_info('Current profile:')} {c_acc(config.active_profile.upper())}\n")
            print("[1] Low    [2] Balanced    [3] Aggressive    [4] Paranoid")
            p = input("\nSelect profile: ").strip()
            profiles = {
                "1": DetectionProfile.LOW,
                "2": DetectionProfile.BALANCED,
                "3": DetectionProfile.AGGRESSIVE,
                "4": DetectionProfile.PARANOID
            }
            if p in profiles:
                config.apply_profile(profiles[p])
                config.save()
                print(c_ok(f"\n✅ Profile changed to: {config.active_profile.upper()}"))
            else:
                print(c_err("\n❌ Invalid choice"))
            input("\nPress Enter to continue...")
        elif choice == "11":
            clear_screen()
            section_header("RANSOMWARE SIMULATION TEST")
            if not daemon.running:
                print(c_err("\n❌ Start real-time monitoring first (Option 1)!"))
            else:
                confirm = input("\nRun test? (y/n): ").lower()
                if confirm == 'y':
                    test_dir = expand_path("~/Desktop")
                    ensure_dir(test_dir)
                    test_files = []
                    print(c_info(f"\nCreating test files in {test_dir}..."))
                    for i in range(7):
                        test_file = os.path.join(test_dir, f"test_encrypted_{i}.encrypted")
                        with open(test_file, 'w') as tf:
                            tf.write(f"Simulated encrypted data {i}" * 100)
                        test_files.append(test_file)
                        time.sleep(0.1)
                    print(c_info("✅ Created 7 test .encrypted files"))
                    print(c_info("   Check the terminal for alerts!"))
                    time.sleep(2)
                    print(c_info("\nCleaning up test files..."))
                    cleaned = 0
                    for tf in test_files:
                        if os.path.exists(tf):
                            try:
                                os.remove(tf)
                                cleaned += 1
                            except Exception:
                                pass
                    quar_items = quarantine_manager.list_all()
                    for item in quar_items:
                        if "test_encrypted" in item['filename']:
                            try:
                                os.remove(item['path'])
                                meta = item['path'] + ".meta"
                                if os.path.exists(meta):
                                    os.remove(meta)
                                cleaned += 1
                            except Exception:
                                pass
                    print(c_ok(f"✅ Cleaned up {cleaned} test file(s)"))
            input("\nPress Enter to continue...")
        elif choice == "0":
            if daemon.running:
                daemon.stop()
            print(c_info("\n👋 Exiting SecureGuard\n"))
            break
        else:
            input(c_err("❌ Invalid option. Press Enter to continue..."))

# ============================================================
# AUTOMATED FULL SCAN MODE
# ============================================================

def run_all_scans():
    """Run every scan in sequence — fully automated, no interaction."""
    print_banner(mode="AUTOMATED FULL SCAN")
    print()

    quick_scan()
    run_deep_scan(auto_quarantine=True)
    persistence_scan()
    spyware_scan()

    stats = state.get_stats()
    print()
    section_header("FINAL SECUREGUARD REPORT")
    print()
    print(score_box(stats, len(state.get_alerts())))

    for alert in state.get_alerts(5):
        print(f"    {c_err('🚨 [' + alert['type'] + ']')} {c_warn(os.path.basename(alert['file']))} "
              f"({c_warn(str(alert['confidence']) + '%')})")

    if stats['threat_score'] >= 70:
        print(c_err(f"\n⚠ HIGH THREAT LEVEL — Review logs at: {expand_path(config.log_dir)}"))
    elif stats['threat_score'] >= 30:
        print(c_warn("\n⚠ MODERATE THREAT LEVEL — Some suspicious items found"))
    else:
        print(c_ok("\n✅ LOW THREAT LEVEL — System appears clean"))

    print()
    section_header("REPORTS GENERATED")
    write_reports(stats)

    level, lc = threat_level(stats['threat_score'])
    print()
    fin_rows = [
        color("Threat Level : ", C.WHITE) + color(level, lc, C.BOLD),
        color("Quarantine   : ", C.WHITE) + c_dim(expand_path(config.quarantine_dir)),
        color("Logs         : ", C.WHITE) + c_dim(expand_path(config.log_dir)),
        color("Backups      : ", C.WHITE) + c_dim(expand_path(config.backup_dir)),
    ]
    print(make_box("SESSION COMPLETE", fin_rows, tcolor=C.GREEN))
    print(color("══════════  Scan complete. SecureGuard terminating.  ══════════", C.CYAN, C.BOLD))
    print()

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Create required directories inside ~/ransomware/
    for directory in [config.config_dir, config.log_dir, config.quarantine_dir, config.backup_dir]:
        ensure_dir(expand_path(directory))

    # Save default config if not exists
    config_path = expand_path(f"{config.config_dir}/config.json")
    if not os.path.exists(config_path):
        config.save()

    # Check for interactive flag
    if '--interactive' in sys.argv or '-i' in sys.argv:
        print_banner(mode="INTERACTIVE MODE")
        print(c_ok("🔒 Initialized. Opening dashboard...\n"))
        try:
            menu()
        except KeyboardInterrupt:
            if daemon.running:
                daemon.stop()
            print(c_info("\n\n👋 SecureGuard terminated\n"))
    else:
        try:
            run_all_scans()
        except KeyboardInterrupt:
            print(c_warn("\n\n⚠ Scan interrupted by user\n"))
