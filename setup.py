#!/usr/bin/env python3
"""
Setup script for MQTT Weather Logger ESP32 project
Initializes the database and installs required dependencies
"""

import subprocess
import sys
import os

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    return True

def initialize_database():
    """Initialize the database with tables and sample data"""
    print("Initializing database...")
    try:
        from init_db import init_db
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    return True

def main():
    print("=== MQTT Weather Logger ESP32 Setup ===")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found. Run this script from the project root directory.")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    print()
    
    # Initialize database
    if not initialize_database():
        return
    
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Run 'python subscriber_db.py' to start the MQTT subscriber")
    print("2. Run 'python publisher.py' to start publishing test data")
    print("3. Run 'python app.py' to start the web dashboard")
    print("4. Open your browser to http://localhost:5000")
    print()
    print("For Wokwi simulation:")
    print("- Upload the project to Wokwi.com")
    print("- The main.py will run on the ESP32 simulator")

if __name__ == "__main__":
    main()
