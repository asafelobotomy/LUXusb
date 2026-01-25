"""
GRUB configuration refresh utility
Scans actual ISOs on USB and regenerates grub.cfg
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from luxusb.utils.grub_installer import GRUBInstaller
from luxusb.utils.distro_manager import Distro
from luxusb.utils.distro_json_loader import DistroJSONLoader
from luxusb.utils.custom_iso import CustomISO
from luxusb.utils.iso_version_parser import ISOVersionParser, ISOVersion

logger = logging.getLogger(__name__)


@dataclass
class OutdatedISO:
    """Information about an outdated ISO"""
    distro: Distro
    current_version: ISOVersion
    available_version: ISOVersion
    current_path: Path
    
    @property
    def upgrade_description(self) -> str:
        """Human-readable upgrade description"""
        return f"{self.distro.name}: {self.current_version.version} → {self.available_version.version}"


class GRUBConfigRefresher:
    """Utility to refresh GRUB configuration based on actual ISOs on disk"""
    
    def __init__(self, efi_mount: Path, data_mount: Path):
        """
        Initialize refresher
        
        Args:
            efi_mount: Mount point of EFI partition
            data_mount: Mount point of data partition
        """
        self.efi_mount = efi_mount
        self.data_mount = data_mount
        self.loader = DistroJSONLoader()
        self.all_distros = self.loader.load_all()
        self.version_parser = ISOVersionParser()
    
    def scan_isos(self) -> Tuple[List[Path], List[Distro], List[CustomISO]]:
        """
        Scan USB drive for ISOs and match to distro metadata
        
        Returns:
            Tuple of (iso_paths, distros, custom_isos)
        """
        iso_dir = self.data_mount / "isos"
        
        if not iso_dir.exists():
            logger.error(f"ISO directory not found: {iso_dir}")
            return ([], [], [])
        
        iso_paths = []
        distros = []
        custom_isos = []
        
        # Scan distro subdirectories
        for distro_subdir in sorted(iso_dir.iterdir()):
            if not distro_subdir.is_dir():
                continue
            
            distro_id = distro_subdir.name
            
            # Handle custom ISOs separately
            if distro_id == 'custom':
                custom_isos = self._scan_custom_isos(distro_subdir)
                continue
            
            # Find distro metadata
            distro = self._find_distro_by_id(distro_id)
            if not distro:
                logger.warning(f"Unknown distro: {distro_id} - skipping")
                continue
            
            # Find ISO file(s) in directory
            iso_files = sorted(distro_subdir.glob("*.iso"))
            
            if not iso_files:
                logger.warning(f"No ISO found in {distro_subdir}")
                continue
            
            # Use most recent ISO if multiple exist
            iso_path = iso_files[-1]  # Assumes alphabetical = chronological
            
            iso_paths.append(iso_path)
            distros.append(distro)
            
            logger.info(f"Found: {distro.name} - {iso_path.name}")
            
            # Warn if multiple ISOs found
            if len(iso_files) > 1:
                logger.warning(
                    f"Multiple ISOs found for {distro.name}, using: {iso_path.name}"
                )
                logger.warning(
                    f"Consider removing old versions: {[f.name for f in iso_files[:-1]]}"
                )
        
        return (iso_paths, distros, custom_isos)
    
    def _find_distro_by_id(self, distro_id: str) -> Optional[Distro]:
        """Find distro metadata by ID"""
        return next((d for d in self.all_distros if d.id == distro_id), None)
    
    def _scan_custom_isos(self, custom_dir: Path) -> List[CustomISO]:
        """Scan custom ISO directory"""
        custom_isos = []
        
        for iso_file in sorted(custom_dir.glob("*.iso")):
            # Create CustomISO object with basic info
            custom_iso = CustomISO(
                filename=iso_file.name,
                display_name=iso_file.stem.replace('-', ' ').replace('_', ' ').title()
            )
            custom_isos.append(custom_iso)
            logger.info(f"Found custom ISO: {custom_iso.display_name}")
        
        return custom_isos
    
    def refresh_config(
        self,
        device: str,
        timeout: int = 10
    ) -> bool:
        """
        Scan ISOs and regenerate GRUB configuration
        
        Args:
            device: Device path (e.g., /dev/sdb)
            timeout: GRUB menu timeout in seconds
            
        Returns:
            True if successful
        """
        logger.info("Scanning USB drive for ISOs...")
        
        iso_paths, distros, custom_isos = self.scan_isos()
        
        if not iso_paths and not custom_isos:
            logger.error("No ISOs found on USB drive")
            return False
        
        logger.info(f"Found {len(iso_paths)} distro ISO(s) and {len(custom_isos)} custom ISO(s)")
        
        # Create GRUB installer
        installer = GRUBInstaller(device, self.efi_mount)
        
        # Regenerate configuration
        logger.info("Regenerating GRUB configuration...")
        success = installer.update_config_with_isos(
            iso_paths,
            distros,
            custom_isos=custom_isos if custom_isos else None,
            timeout=timeout
        )
        
        if success:
            logger.info("GRUB configuration refreshed successfully")
        else:
            logger.error("Failed to refresh GRUB configuration")
        
        return success
    
    def verify_config_freshness(self) -> Tuple[bool, str]:
        """
        Check if GRUB config matches actual ISOs on disk
        
        Returns:
            Tuple of (is_fresh, message)
        """
        grub_cfg = self.efi_mount / "boot" / "grub" / "grub.cfg"
        
        if not grub_cfg.exists():
            return (False, "GRUB config not found")
        
        # Read current config
        try:
            with open(grub_cfg, 'r') as f:
                config_content = f.read()
        except (OSError, IOError) as e:
            return (False, f"Failed to read config: {e}")
        
        # Scan actual ISOs
        iso_paths, distros, custom_isos = self.scan_isos()
        
        # Check if all ISOs are referenced in config
        missing = []
        for iso_path, distro in zip(iso_paths, distros):
            # Extract relative path for GRUB
            parts = iso_path.parts
            try:
                isos_idx = parts.index('isos')
                iso_rel = '/' + '/'.join(parts[isos_idx:])
            except ValueError:
                iso_rel = f"/{iso_path.name}"
            
            if iso_rel not in config_content:
                missing.append(f"{distro.name} ({iso_path.name})")
        
        for custom_iso in custom_isos:
            custom_rel = f"/isos/custom/{custom_iso.filename}"
            if custom_rel not in config_content:
                missing.append(f"{custom_iso.display_name} (custom)")
        
        # Check for stale references
        stale = []
        import re
        iso_refs = re.findall(r'/isos/[^"\']+\.iso', config_content)
        
        for ref in iso_refs:
            # Convert GRUB path to filesystem path
            fs_path = self.data_mount / ref[1:]  # Remove leading /
            if not fs_path.exists():
                stale.append(ref)
        
        if missing and stale:
            return (
                False,
                f"Config outdated: {len(missing)} missing, {len(stale)} stale references"
            )
        elif missing:
            return (
                False,
                f"Config missing {len(missing)} ISO(s): {', '.join(missing)}"
            )
        elif stale:
            return (
                False,
                f"Config has {len(stale)} stale reference(s): {', '.join(stale)}"
            )
        else:
            return (True, "Config up to date")
    
    def check_outdated_isos(self) -> List[OutdatedISO]:
        """
        Check if ISOs on USB are outdated compared to available versions
        
        Returns:
            List of outdated ISOs with upgrade information
        """
        outdated = []
        
        # Scan current ISOs on USB
        iso_paths, distros, _ = self.scan_isos()
        
        for iso_path, distro in zip(iso_paths, distros):
            # Parse current ISO version
            current_version = self.version_parser.parse(iso_path.name)
            if not current_version:
                logger.warning(f"Could not parse version from: {iso_path.name}")
                continue
            
            # Get available version from metadata
            available_version = self._get_latest_available_version(distro, current_version)
            if not available_version:
                continue
            
            # Compare versions
            try:
                if self.version_parser.is_newer(available_version, current_version):
                    outdated.append(OutdatedISO(
                        distro=distro,
                        current_version=current_version,
                        available_version=available_version,
                        current_path=iso_path
                    ))
                    logger.info(
                        f"Outdated: {distro.name} {current_version.version} "
                        f"(available: {available_version.version})"
                    )
            except ValueError as e:
                logger.debug(f"Cannot compare versions for {distro.name}: {e}")
        
        return outdated
    
    def _get_latest_available_version(
        self,
        distro: Distro,
        current_version: ISOVersion
    ) -> Optional[ISOVersion]:
        """
        Get latest available version from distro metadata
        
        Args:
            distro: Distro object
            current_version: Current ISO version on USB
            
        Returns:
            Latest available ISOVersion or None
        """
        if not distro.releases:
            return None
        
        # Parse available releases
        available_versions = []
        for release in distro.releases:
            # Try to construct filename from release data
            # This is heuristic-based and may need adjustment per distro
            iso_url = release.iso_url
            if iso_url:
                filename = Path(iso_url).name
                parsed = self.version_parser.parse(filename)
                if parsed:
                    # Match variant and architecture
                    if (parsed.variant == current_version.variant and
                        parsed.architecture == current_version.architecture):
                        available_versions.append(parsed)
        
        if not available_versions:
            return None
        
        # Return the latest version
        latest = max(available_versions, key=lambda v: v.sort_key)
        return latest

