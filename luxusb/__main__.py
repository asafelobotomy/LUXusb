#!/usr/bin/env python3
"""
Main entry point for LUXusb application
"""

import sys
import os
import logging
import subprocess
import shutil
import threading
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

from luxusb.constants import PathPattern, ConfigKeys


def setup_logging() -> None:
    """Configure application logging"""
    log_dir = Path.home() / PathPattern.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / PathPattern.LOG_FILE
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_requirements() -> bool:
    """Check if system meets minimum requirements"""
    logger = logging.getLogger(__name__)
    
    # Check Python version
    if sys.version_info < (3, 10):
        logger.error("Python 3.10 or higher is required")
        return False
    
    # Check if running on Linux
    if sys.platform not in ['linux', 'linux2']:
        logger.error("This application only runs on Linux")
        return False
    
    # Check for required system tools
    required_tools = ['lsblk', 'parted', 'mkfs.vfat', 'mkfs.ext4']
    missing_tools = []
    
    for tool in required_tools:
        if shutil.which(tool) is None:
            missing_tools.append(tool)
    
    if missing_tools:
        logger.error(f"Missing required system tools: {', '.join(missing_tools)}")
        logger.info("Install them using your package manager")
        return False
    
    return True


def auto_update_metadata_background(on_complete_callback=None) -> None:
    """
    Automatically update distro metadata with GPG verification in background.
    Respects config settings for frequency and whether to auto-update.
    
    Args:
        on_complete_callback: Optional callback function(success_count: int) called on completion
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Check config if auto-update is enabled
        from luxusb.config import Config
        config = Config()
        
        if not config.get(ConfigKeys.Metadata.AUTO_UPDATE_ON_STARTUP, default=True):
            logger.info("Automatic metadata updates disabled in config")
            return
        
        update_frequency_days = config.get(ConfigKeys.Metadata.UPDATE_FREQUENCY_DAYS, default=7)
        
        # Check if we should update based on frequency
        cache_dir = Path.home() / PathPattern.CACHE_DIR
        cache_dir.mkdir(parents=True, exist_ok=True)
        update_marker = cache_dir / PathPattern.UPDATE_MARKER_FILE
        
        should_update = True
        if update_marker.exists() and update_frequency_days > 0:
            try:
                with open(update_marker, 'r') as f:
                    data = json.load(f)
                    last_update = datetime.fromisoformat(data['timestamp'])
                    days_since = (datetime.now() - last_update).days
                    
                    if days_since < update_frequency_days:
                        should_update = False
                        logger.info(f"Metadata updated {days_since} days ago (frequency: {update_frequency_days} days), skipping")
            except Exception as e:
                logger.debug(f"Could not read update marker: {e}")
        
        if not should_update:
            return
        
        logger.info("Starting automatic metadata update with GPG verification...")
        
        from luxusb.utils.distro_updater import DistroUpdater
        updater = DistroUpdater()
        
        # Set timeout from config
        updater.session.timeout = config.get(ConfigKeys.Metadata.UPDATE_TIMEOUT, default=30)
        
        results = updater.update_all()
        
        # Log results with GPG status
        success_count = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"Metadata update complete: {success_count}/{total} distros updated")
        
        # Count GPG verified distros by checking the JSON files
        gpg_verified_count = 0
        distros_dir = Path(__file__).parent / "data" / "distros"
        for json_file in distros_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    for release in data.get('releases', []):
                        if release.get('gpg_verified', False):
                            gpg_verified_count += 1
                            break  # Count distro only once
            except:
                pass
        
        logger.info(f"GPG verification status: {gpg_verified_count}/{total} distros verified")
        
        # Save update timestamp
        with open(update_marker, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'success_count': success_count,
                'total': total,
                'gpg_verified': gpg_verified_count
            }, f)
        
        # Call completion callback if provided
        if on_complete_callback and success_count > 0:
            try:
                on_complete_callback(success_count)
            except Exception as cb_error:
                logger.debug(f"Update callback error: {cb_error}")
        
    except Exception as e:
        logger.warning(f"Background metadata update failed: {e}")
        logger.debug("App will continue with existing metadata")


def check_root_and_elevate() -> bool:
    """
    Check if running as root, if not try to elevate using pkexec
    Returns True if running as root or successfully elevated, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check if already running as root
    if os.geteuid() == 0:
        logger.info("Running with root privileges")
        return True
    
    logger.info("Not running as root, attempting privilege escalation...")
    
    # Check if pkexec is available
    if not shutil.which('pkexec'):
        logger.error("pkexec not found. Please install polkit or run with sudo.")
        print("\n" + "="*60)
        print("ERROR: Root privileges required")
        print("="*60)
        print("\nThis application requires root privileges to manage USB devices.")
        print("\nPlease either:")
        print("  1. Install polkit: sudo pacman -S polkit")
        print("  2. Run with sudo: sudo python -m luxusb")
        print("="*60 + "\n")
        return False
    
    # Re-execute with pkexec
    logger.info("Requesting elevation via pkexec...")
    
    # Get the Python interpreter path (absolute)
    python_exe = os.path.abspath(sys.executable)
    
    # Get the script directory to run as module
    script_dir = Path(__file__).parent.parent
    
    # Build command: python -m luxusb
    module_args = [python_exe, "-m", "luxusb"]
    
    # Add any command line arguments
    if len(sys.argv) > 1:
        module_args.extend(sys.argv[1:])
    
    try:
        # Set environment for pkexec
        env = os.environ.copy()
        
        # Preserve critical environment variables for GUI
        preserve_vars = ['DISPLAY', 'XAUTHORITY', 'DBUS_SESSION_BUS_ADDRESS', 
                        'XDG_RUNTIME_DIR', 'WAYLAND_DISPLAY']
        
        env_args = []
        for var in preserve_vars:
            if var in env:
                env_args.extend([f"{var}={env[var]}"])
        
        # Add script directory to PYTHONPATH so module can be imported
        if 'PYTHONPATH' in env:
            env_args.append(f"PYTHONPATH={script_dir}:{env['PYTHONPATH']}")
        else:
            env_args.append(f"PYTHONPATH={script_dir}")
        
        # Launch with pkexec (GUI authentication dialog)
        result = subprocess.run(
            ['pkexec', 'env'] + env_args + module_args
        )
        
        # Exit this process since pkexec launched a new one
        sys.exit(result.returncode)
        
    except Exception as e:
        logger.error(f"Failed to elevate privileges: {e}")
        print("\n" + "="*60)
        print("ERROR: Failed to elevate privileges")
        print("="*60)
        print(f"\n{e}")
        print("\nPlease run with sudo: sudo python -m luxusb")
        print("="*60 + "\n")
        return False


def main() -> int:
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting LUXusb")
    
    # Check requirements first
    if not check_requirements():
        logger.error("System requirements not met. Exiting.")
        return 1
    
    # Check root privileges and elevate if needed
    if not check_root_and_elevate():
        logger.error("Failed to obtain root privileges. Exiting.")
        return 1
    
    # Auto-update distro metadata with GPG verification in background
    # This runs once per week to keep checksums and GPG status fresh
    update_thread = threading.Thread(
        target=auto_update_metadata_background,
        daemon=True,
        name="MetadataUpdater"
    )
    update_thread.start()
    logger.info("Started background metadata update (runs weekly)")
    
    try:
        # Import GUI here to avoid issues if requirements not met
        from luxusb.gui.main_window import LUXusbApplication
        
        app = LUXusbApplication()
        return app.run(sys.argv)
        
    except ImportError as e:
        logger.error(f"Failed to import GUI modules: {e}")
        logger.error("Make sure GTK4 and PyGObject are installed")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
