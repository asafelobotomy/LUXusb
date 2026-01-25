# ISO Update Strategy & GRUB Configuration Management

## Current Behavior

### When GRUB Config is Regenerated:
1. **ERASE Mode**: Full USB creation - GRUB config generated with all ISOs
2. **APPEND Mode**: Adding new ISOs - GRUB config regenerated with all ISOs
3. **Manual Fix**: Running `fix_grub_config.py` script

### Problem Scenarios:

#### Scenario 1: App-Based Updates (✅ Works)
User workflow:
1. Runs LUXusb app
2. Selects "Add ISOs" (append mode)
3. Downloads new Arch Linux 2026.07.01
4. **GRUB config auto-regenerates** with updated paths ✅

#### Scenario 2: Manual File Replacement (❌ Breaks)
User workflow:
1. Mounts USB manually
2. Deletes `/isos/arch/arch-2026.01.01.iso`
3. Copies new `/isos/arch/arch-2026.07.01.iso`
4. **GRUB config still references old filename** ❌
5. Boot fails - file not found

## Solutions Implemented

### Solution 1: Smart ISO Scanning in GRUB Config
**Status**: Can be implemented

Instead of hardcoding exact filenames, scan for ISOs at boot time:
```bash
# Current (hardcoded):
loopback loop /isos/arch/arch-2026.01.01.iso

# Better (pattern-based):
for isofile in /isos/arch/*.iso; do
    if [ -f "$isofile" ]; then
        loopback loop "$isofile"
        break
    fi
done
```

**Pros**: Resilient to filename changes
**Cons**: GRUB scripting complexity, slightly slower boot

### Solution 2: Auto-Detect on Boot (Recommended)
Create a GRUB helper script that scans `/isos/` at boot and dynamically generates menu entries.

**Implementation**: Add to GRUB config:
```bash
# Scan for ISOs and auto-generate menu entries
for distro_dir in /isos/*; do
    distro_name=$(basename "$distro_dir")
    for iso in "$distro_dir"/*.iso; do
        if [ -f "$iso" ]; then
            menuentry "Auto: $distro_name" {
                loopback loop "$iso"
                # Boot logic...
            }
        fi
    done
done
```

### Solution 3: Re-Sync Command (Quick Fix)
**Status**: ✅ Already Implemented

Users can run the fix script to regenerate config:
```bash
sudo .venv/bin/python fix_grub_config.py
```

This scans actual ISOs on disk and regenerates GRUB config.

### Solution 4: State File Verification
**Status**: Partial - state file exists but not used for config regeneration

Add logic to check if ISO files match state file on boot/mount.

## Recommendations

### For Users:

#### Recommended: Use the App
1. Run LUXusb in append mode
2. Select new distro versions
3. App handles everything automatically ✅

#### If Manual Updates Needed:
1. Mount USB partitions
2. Replace/add ISO files
3. Run config re-sync:
   ```bash
   sudo mkdir -p /tmp/luxusb-mount/{efi,data}
   sudo mount /dev/sdX2 /tmp/luxusb-mount/efi
   sudo mount /dev/sdX3 /tmp/luxusb-mount/data
   cd /path/to/LUXusb
   sudo .venv/bin/python fix_grub_config.py
   sudo umount /tmp/luxusb-mount/{efi,data}
   ```

### For Developers:

#### Immediate (Phase 3.6):
- [x] Document the re-sync workflow
- [ ] Add "Refresh GRUB Config" button in GUI
- [ ] Auto-detect stale config (compare state file with actual ISOs)

#### Future Enhancement (Phase 4):
- [ ] Implement dynamic ISO scanning in GRUB config
- [ ] Add filesystem watcher for ISO directory changes
- [ ] One-click "Update All Distros" feature

## Technical Details

### GRUB Config Generation Flow:
```
1. Scan /isos/{distro_id}/ directories
2. Find all *.iso files
3. Match ISO files to distro metadata
4. Generate menuentry for each ISO
5. Write to /boot/grub/grub.cfg
```

### ISO Path Format:
- **Absolute on host**: `/tmp/luxusb-mount/data/isos/arch/arch.iso`
- **Relative in GRUB**: `/isos/arch/arch.iso`
- **Pattern match**: `/isos/arch/*.iso`

### File Naming Conventions:
Most distros use date-based versioning:
- Arch: `archlinux-YYYY.MM.DD-x86_64.iso`
- Ubuntu: `ubuntu-YY.MM-desktop-amd64.iso`
- Fedora: `Fedora-Workstation-Live-x86_64-XX.iso`

Pattern matching must account for varying formats.

## Testing Checklist

- [ ] Create USB with Arch 2026.01.01
- [ ] Boot and verify it works
- [ ] Use append mode to add Arch 2026.07.01
- [ ] Verify GRUB config updated automatically
- [ ] Manually replace ISO file
- [ ] Run fix_grub_config.py
- [ ] Verify boot works again

## Related Files

- `luxusb/core/workflow.py` - Workflow orchestration
- `luxusb/utils/grub_installer.py` - GRUB config generation
- `fix_grub_config.py` - Manual config re-sync script

## Future Consideration: Version Management

Could implement smart version tracking:
- Keep last 2 versions of each distro
- Auto-cleanup old versions
- Warn user if ISO is outdated (>6 months old)
