#!/usr/bin/env python3
"""
MediSync Quick Start Script
Installs dependencies and launches the application
Run this file to get started immediately
"""

import subprocess
import sys
import os
from pathlib import Path


def print_header():
    """Print welcome header"""
    print("\n" + "="*70)
    print("🏥 MediSync - Multi-Agent Healthcare Assistant".center(70))
    print("="*70 + "\n")


def check_python_version():
    """Verify Python version compatibility"""
    print("✓ Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected\n")


def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ Error: requirements.txt not found")
        sys.exit(1)
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Dependencies installed successfully\n")
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies")
        sys.exit(1)


def verify_files():
    """Verify all required files exist"""
    print("📋 Verifying project files...")
    required_files = [
        "medisync_app.py",
        "patient_knowledge_graph.py",
        "agent_analyzer.py",
        "agent_pharmacist.py",
        "agent_care_coordinator.py",
        "discharge_summaries.csv"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (optional)")
            if file != "discharge_summaries.csv":
                missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Error: Missing required files: {', '.join(missing_files)}")
        sys.exit(1)
    
    print()


def launch_app():
    """Launch Streamlit application"""
    print("🚀 Launching MediSync Application...\n")
    print("="*70)
    print("The app should open in your browser shortly.")
    print("If not, visit: http://localhost:8501")
    print("="*70 + "\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "medisync_app.py"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Application closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        sys.exit(1)


def print_usage_tips():
    """Print helpful usage tips"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         🎯 GETTING STARTED TIPS                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  1. LOAD PATIENT DATA:                                                    ║
║     • Go to "Upload Patient" tab                                          ║
║     • Click "Load Mock Patient" for quick demo                            ║
║                                                                            ║
║  2. VIEW DASHBOARD:                                                       ║
║     • See patient overview                                                ║
║     • Review medications and interactions                                 ║
║     • Check follow-up appointments                                        ║
║                                                                            ║
║  3. RUN AGENT PIPELINE:                                                   ║
║     • Go to "Agent Orchestration"                                         ║
║     • Click "Run Full Pipeline"                                           ║
║     • Watch all three agents work together                                ║
║                                                                            ║
║  4. CHAT WITH CARE COORDINATOR:                                           ║
║     • Go to "Care Coordinator Chat"                                       ║
║     • Ask questions about recovery, medications, etc.                    ║
║                                                                            ║
║  5. EXPLORE FEATURES:                                                     ║
║     • Medication Review: See detailed drug interactions                  ║
║     • Reports & Export: Download patient data                             ║
║     • Dashboard: Real-time monitoring and metrics                         ║
║                                                                            ║
║  📚 For more information, see README.md                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


def main():
    """Main entry point"""
    try:
        print_header()
        check_python_version()
        verify_files()
        install_dependencies()
        print_usage_tips()
        launch_app()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
