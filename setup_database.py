#!/usr/bin/env python3
"""
Setup script for Database Routing System
==========================================
This script helps you:
1. Install required dependencies
2. Configure Neon DB connection
3. Initialize database tables
4. Test the connection
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# Step 1: Install dependencies
def install_dependencies():
    """Install required Python packages."""
    print_header("STEP 1: INSTALL DEPENDENCIES")
    
    print("Installing database and routing dependencies...\n")
    
    requirements_file = "requirements-db.txt"
    if not os.path.exists(requirements_file):
        print_error(f"{requirements_file} not found")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file, "-q"])
        print_success("All dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

# Step 2: Configure .env file
def configure_env():
    """Guide user through configuring .env file."""
    print_header("STEP 2: CONFIGURE NEON DB CONNECTION")
    
    env_file = ".env"
    
    print("You'll need to get your Neon DB connection string from:")
    print(f"  {Colors.BLUE}https://console.neon.tech/{Colors.END}\n")
    
    print("Steps:")
    print("  1. Go to Neon Console")
    print("  2. Select your project")
    print("  3. Go to 'Connection Details'")
    print("  4. Copy the connection string\n")
    
    if os.path.exists(env_file):
        response = input(f"{Colors.YELLOW}Found existing .env file. Overwrite? (y/N): {Colors.END}").strip().lower()
        if response != "y":
            print_info("Skipping .env configuration")
            return True
    
    print("\nEnter your Neon DB credentials:\n")
    
    # Get database URL
    while True:
        db_url = input(f"  Database URL: ").strip()
        if db_url and "postgresql://" in db_url:
            break
        else:
            print_error("Invalid URL. Must be PostgreSQL connection string.")
    
    # Alternative: individual components
    print("\n  Or enter individual components:\n")
    
    db_host = input("  Host (e.g., ep-xxxxx.us-east-1.sql.neon.tech): ").strip()
    db_port = input("  Port (default 5432): ").strip() or "5432"
    db_name = input("  Database name: ").strip()
    db_user = input("  User: ").strip()
    db_password = input("  Password: ").strip()
    
    # Write .env file
    env_content = f"""# ============================================================================
# NEON DATABASE CONFIGURATION
# ============================================================================
DATABASE_URL={db_url}

# Or individual components:
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# ============================================================================
# DEPARTMENT CONFIGURATION
# ============================================================================
DEPT_FIRE=fire_complaints
DEPT_POLICE=police_complaints
DEPT_HEALTH=health_complaints
DEPT_WATER=water_complaints
DEPT_ELECTRICITY=electricity_complaints
DEPT_GENERAL=general_complaints

# ============================================================================
# BACKEND CONFIGURATION
# ============================================================================
BACKEND_API_URL=http://localhost:8000

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO
DEBUG=False
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print_success(f"Created {env_file} with your configuration")
    return True

# Step 3: Test database connection
def test_connection():
    """Test connection to database."""
    print_header("STEP 3: TEST DATABASE CONNECTION")
    
    try:
        # Load environment
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Try to connect
        import psycopg2
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            # Build from components
            db_host = os.getenv("DB_HOST")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME")
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            
            if not all([db_host, db_name, db_user, db_password]):
                print_error("Database credentials not configured in .env")
                return False
            
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
        
        print("Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.close()
        
        print_success("Successfully connected to Neon DB!")
        return True
    
    except ImportError:
        print_error("psycopg2 not installed. Run step 1 first.")
        return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_info("Check your .env file and database URL")
        return False

# Step 4: Initialize database tables
def init_database_tables():
    """Initialize database tables."""
    print_header("STEP 4: INITIALIZE DATABASE TABLES")
    
    try:
        from database_router import init_database, init_routing
        
        print("Initializing database tables...\n")
        
        if init_database():
            print_success("Database tables created/verified")
        else:
            print_error("Failed to create database tables")
            return False
        
        if init_routing():
            print_success("Routing system initialized")
        else:
            print_warning("Routing system initialization failed (non-critical)")
        
        return True
    
    except ImportError:
        print_error("database_router module not found")
        print_info("Make sure you're in the correct directory")
        return False
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        return False

# Step 5: Verify setup
def verify_setup():
    """Verify all components are working."""
    print_header("STEP 5: VERIFY SETUP")
    
    checks = {
        "psycopg2": False,
        "python-dotenv": False,
        "database_router": False,
        ".env file": False,
        "Database connection": False,
    }
    
    # Check psycopg2
    try:
        import psycopg2
        checks["psycopg2"] = True
    except ImportError:
        pass
    
    # Check python-dotenv
    try:
        from dotenv import load_dotenv
        checks["python-dotenv"] = True
    except ImportError:
        pass
    
    # Check database_router
    try:
        import database_router
        checks["database_router"] = True
    except ImportError:
        pass
    
    # Check .env file
    if os.path.exists(".env"):
        checks[".env file"] = True
    
    # Check database connection
    try:
        from database_router import get_db_status
        status = get_db_status()
        if status.get("status") == "connected":
            checks["Database connection"] = True
    except:
        pass
    
    # Print results
    for component, status in checks.items():
        if status:
            print_success(f"{component}: OK")
        else:
            print_error(f"{component}: FAILED")
    
    all_ok = all(checks.values())
    
    if all_ok:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED!{Colors.END}")
        print("\nYou can now run:")
        print(f"  {Colors.BLUE}python interactive_voice_to_layer3_enhanced.py{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED{Colors.END}")
        print("\nPlease review the errors above and try again.\n")
        return False

# Main
def main():
    print_header("DATABASE SETUP FOR VOICE COMPLAINT SYSTEM")
    
    steps = [
        ("Install Dependencies", install_dependencies),
        ("Configure .env", configure_env),
        ("Test Connection", test_connection),
        ("Initialize Databases", init_database_tables),
        ("Verify Setup", verify_setup),
    ]
    
    for i, (name, func) in enumerate(steps, 1):
        print_info(f"[{i}/{len(steps)}] {name}")
        
        if not func():
            print_error(f"Setup incomplete. {name} failed.")
            response = input(f"\n{Colors.YELLOW}Continue anyway? (y/N): {Colors.END}").strip().lower()
            if response != "y":
                sys.exit(1)
        
        print()
    
    print_header("SETUP COMPLETE")
    print("Your voice complaint system is ready with database routing!")
    print("\nNext steps:")
    print("  1. Review the .env file and update if needed")
    print("  2. Verify database credentials are correct")
    print("  3. Run the voice system:")
    print(f"     {Colors.BLUE}python interactive_voice_to_layer3_enhanced.py{Colors.END}\n")

if __name__ == "__main__":
    main()
