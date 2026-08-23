#!/usr/bin/env python3
"""
Ransomware Simulator - Educational Purpose Only
================================================
This creates harmless test files with ransomware-like extensions
for testing SecureGuard detection capabilities.

SAFETY FEATURES:
- Only creates .locked.test files (harmless)
- Does NOT encrypt or modify existing files
- All files are in a dedicated test directory
- Files contain plain text, not real encryption
- Can be easily deleted with cleanup function

WARNING: This is for authorized security testing ONLY!
"""

import os
import time
import random
import string
import shutil
from datetime import datetime

class RansomwareSimulator:
    """Safe ransomware simulator for educational testing"""
    
    def __init__(self):
        self.test_dir = os.path.expanduser("~/RansomwareTest")
        self.files_created = []
        
    def create_test_files(self, count=50):
        """
        Create simulated ransomware files.
        Each file has .locked.test extension and contains fake ransom notes.
        """
        print("=" * 60)
        print("  RANSOMWARE SIMULATOR - Educational Purpose Only")
        print("=" * 60)
        print()
        
        # Create test directory
        os.makedirs(self.test_dir, exist_ok=True)
        print(f"📁 Creating test files in: {self.test_dir}")
        print()
        
        # Ransom note templates
        ransom_notes = [
            "!!! YOUR FILES HAVE BEEN ENCRYPTED !!!\n\nTo decrypt your files, you need to pay 0.5 Bitcoin.\nWallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n\nYou have 48 hours to pay or your files will be lost forever!",
            
            "⚠️ ALL YOUR DATA IS ENCRYPTED ⚠️\n\nContact us at: decrypt@onionmail.com\n\nPayment: 1 BTC to wallet: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy\n\nYour unique ID: {id}",
            
            "🔐 FILES ENCRYPTED WITH RSA-2048 🔐\n\nYour documents, photos, databases have been encrypted.\n\nTo recover your files:\n1. Visit: http://ransomware.onion/{id}\n2. Pay 0.5 BTC\n3. Receive decryption key\n\nDO NOT CONTACT AUTHORITIES!",
            
            "URGENT! YOUR FILES ARE LOCKED!\n\nWe have encrypted ALL your personal files.\n\nPayment required: 2 BTC\n\nDecryption instructions will be sent after payment.\n\nWallet: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            
            "✋ STOP! Your files are encrypted ✋\n\nWhat happened?\n- Your files were encrypted with military-grade encryption\n- You have 72 hours to pay\n- If you don't pay, files will be deleted forever\n\nContact: ransom@onionmail.com\n\nYour ID: {id}"
        ]
        
        # File name patterns (different types to simulate real ransomware)
        file_types = [
            "document", "photo", "video", "personal", "work", "project",
            "data", "backup", "confidential", "financial", "tax", "invoice",
            "contract", "agreement", "report", "presentation", "spreadsheet",
            "database", "archive", "important"
        ]
        
        print(f"🔨 Creating {count} simulated ransomware files...")
        print()
        
        for i in range(count):
            # Generate random file name
            file_type = random.choice(file_types)
            if random.random() > 0.5:
                # Some with numbers
                filename = f"{file_type}_{random.randint(1, 100)}.locked.test"
            else:
                # Some with random IDs
                id_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                filename = f"{file_type}_{id_suffix}.locked.test"
            
            filepath = os.path.join(self.test_dir, filename)
            
            # Add random content (simulating encrypted data)
            with open(filepath, 'w') as f:
                # Randomly choose between ransom note or "encrypted" data
                if random.random() < 0.3:  # 30% chance of ransom note
                    note = random.choice(ransom_notes)
                    note_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    note = note.format(id=note_id)
                    f.write(note)
                else:
                    # Simulated "encrypted" data
                    encrypted_data = []
                    for _ in range(20 + random.randint(0, 30)):
                        line = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*()", k=64))
                        encrypted_data.append(line)
                    f.write("\n".join(encrypted_data))
            
            self.files_created.append(filepath)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  ✅ Created {i + 1} files")
        
        print()
        print(f"✅ Successfully created {count} test files")
        print()
        
        # Create some additional ransom note files
        self._create_ransom_notes()
        
        # Create some files with double extensions (common ransomware pattern)
        self._create_double_extension_files()
        
        return self.files_created
    
    def _create_ransom_notes(self):
        """Create standalone ransom note files"""
        note_dir = os.path.join(self.test_dir, "ransom_notes")
        os.makedirs(note_dir, exist_ok=True)
        
        note_files = [
            ("README_DECRYPT.txt", "!!! YOUR FILES ARE ENCRYPTED !!!\n\nPay 0.5 BTC to recover your files."),
            ("HOW_TO_DECRYPT.html", "<html><body><h1>FILES ENCRYPTED</h1><p>Pay ransom to recover.</p></body></html>"),
            ("DECRYPT_INSTRUCTIONS.txt", "To decrypt, send 1 BTC to wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"),
            ("PAYMENT_INFO.txt", "Payment required: 0.5 BTC\nWallet: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"),
            ("RECOVER_FILES.txt", "Your files can be recovered. Follow instructions."),
        ]
        
        for filename, content in note_files:
            filepath = os.path.join(note_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            self.files_created.append(filepath)
        
        print(f"  📝 Created {len(note_files)} ransom note files")
    
    def _create_double_extension_files(self):
        """Create files with double extensions (common ransomware pattern)"""
        double_dir = os.path.join(self.test_dir, "double_extensions")
        os.makedirs(double_dir, exist_ok=True)
        
        double_files = [
            ("document.pdf.lockbit", "This is a simulated encrypted PDF file"),
            ("photo.jpg.encrypted", "This is a simulated encrypted image"),
            ("video.mp4.locked", "This is a simulated encrypted video"),
            ("database.sql.conti", "This is a simulated encrypted database"),
            ("presentation.pptx.wncry", "This is a simulated encrypted presentation"),
            ("spreadsheet.xlsx.ryuk", "This is a simulated encrypted spreadsheet"),
            ("archive.zip.dharma", "This is a simulated encrypted archive"),
            ("backup.tar.gz.phobos", "This is a simulated encrypted backup"),
            ("report.pdf.lockbit", "This is a simulated encrypted report"),
            ("contract.docx.encrypted", "This is a simulated encrypted contract"),
        ]
        
        for filename, content in double_files:
            filepath = os.path.join(double_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            self.files_created.append(filepath)
        
        print(f"  📂 Created {len(double_files)} double-extension files")
    
    def show_stats(self):
        """Display statistics about created files"""
        print()
        print("=" * 60)
        print("  FILE CREATION STATISTICS")
        print("=" * 60)
        print()
        print(f"📊 Total files created: {len(self.files_created)}")
        print(f"📁 Location: {self.test_dir}")
        print()
        print("📋 File types created:")
        print("  • .locked.test files: 50 (simulated ransomware)")
        print("  • Ransom note files: 5")
        print("  • Double-extension files: 10")
        print()
        print("🔬 Files will be detected by SecureGuard as:")
        print("  • Ransomware extensions (.locked, .encrypted, .lockbit, etc.)")
        print("  • Ransom note patterns (README, DECRYPT, etc.)")
        print("  • High entropy content (random data)")
    
    def run_scan(self):
        """Run SecureGuard after creating files"""
        print()
        print("=" * 60)
        print("  RUNNING SECUREGUARD SCAN")
        print("=" * 60)
        print()
        
        # Import and run SecureGuard
        try:
            import subprocess
            subprocess.run(["python3", "secureguard.py"], check=True)
        except Exception as e:
            print(f"❌ Error running SecureGuard: {e}")
            print("  Make sure secureguard.py is in the current directory")
    
    def cleanup(self):
        """Delete all created test files"""
        print()
        print("🧹 Cleaning up test files...")
        
        # Remove test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"✅ Removed {self.test_dir}")
        else:
            print("ℹ️ No test files to clean up")
        
        self.files_created = []

def interactive_menu():
    """Interactive menu for the simulator"""
    sim = RansomwareSimulator()
    
    while True:
        print("\n" + "=" * 60)
        print("  RANSOMWARE SIMULATOR - Interactive Menu")
        print("=" * 60)
        print()
        print("1. Create 50 ransomware simulation files")
        print("2. Create custom number of files")
        print("3. Show statistics")
        print("4. Run SecureGuard scan")
        print("5. Clean up test files")
        print("6. Exit")
        print()
        
        choice = input("👉 Select option: ").strip()
        
        if choice == "1":
            sim.create_test_files(50)
            sim.show_stats()
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            try:
                count = int(input("How many files to create? (1-200): "))
                count = max(1, min(200, count))
                sim.create_test_files(count)
                sim.show_stats()
            except ValueError:
                print("❌ Invalid number")
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            sim.show_stats()
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            sim.run_scan()
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            sim.cleanup()
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            print("\n👋 Exiting simulator")
            break
        
        else:
            print("❌ Invalid option")
            input("\nPress Enter to continue...")

def main():
    """Main entry point"""
    print("=" * 60)
    print("  RANSOMWARE SIMULATOR - Educational Purpose Only")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This tool is for authorized security testing ONLY!")
    print("   • Creates harmless .locked.test files")
    print("   • Does NOT encrypt real files")
    print("   • All files are in ~/RansomwareTest/")
    print("   • Can be cleaned up easily")
    print()
    print("🔬 Purpose: Test SecureGuard ransomware detection")
    print()
    
    # Check if SecureGuard exists
    if not os.path.exists("secureguard.py"):
        print("❌ Warning: secureguard.py not found in current directory")
        print("   Make sure you're in the right directory")
        print()
    
    interactive_menu()

if __name__ == "__main__":
    main()
