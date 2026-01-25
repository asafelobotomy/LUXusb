# Phase 2 Implementation Plan

## Overview

Phase 2 focuses on enhancing flexibility, reliability, and user control through dynamic distribution management and improved download capabilities.

## Goals

1. **Multiple ISO Support** - Install multiple distributions on one USB drive
2. **Resume Interrupted Downloads** - Pause/resume large ISO downloads
3. **Mirror Selection** - User-configurable mirror preferences
4. **Dynamic Distribution Metadata** - Load distro info from JSON/API

## Features Breakdown

### 1. Multiple ISO Support

**Objective**: Allow users to install multiple Linux distributions on a single USB drive with GRUB multi-boot menu.

**Technical Requirements**:
- [ ] Partition layout for multiple ISOs
- [ ] ISO storage directory structure (`/iso/ubuntu.iso`, `/iso/fedora.iso`)
- [ ] GRUB menu generation for multiple entries
- [ ] Space calculation and validation
- [ ] Multi-selection UI in distro page

**Architecture Changes**:
```python
# New data structures
@dataclass
class ISOSelection:
    distro: Distro
    release: DistroRelease
    install_path: str  # e.g., "/iso/ubuntu-24.04.iso"
    
class MultiISOWorkflow(LUXusbWorkflow):
    def __init__(self, device: USBDevice, selections: List[ISOSelection]):
        self.selections = selections
        # Calculate total space needed
        # Partition with larger data partition
```

**UI Changes**:
- Checkbox selection on distro page (instead of single selection)
- Space calculator showing total size vs USB capacity
- Installation summary showing all selected distros

**Implementation Priority**: HIGH (core feature)

---

### 2. Resume Interrupted Downloads

**Objective**: Support HTTP range requests to resume partial downloads.

**Technical Requirements**:
- [ ] HTTP Range header support
- [ ] Partial file management (`.part` files)
- [ ] Resume metadata storage (bytes downloaded, checksum progress)
- [ ] UI controls (pause/resume buttons)
- [ ] Integrity verification after resume

**Architecture Changes**:
```python
class ISODownloader:
    def download_with_resume(
        self,
        url: str,
        dest_path: Path,
        progress_callback: Callable[[int, int], None],
        pause_event: Event,
    ) -> bool:
        """Download with pause/resume support"""
        part_file = dest_path.with_suffix('.part')
        
        # Check existing partial download
        if part_file.exists():
            downloaded_bytes = part_file.stat().st_size
            headers = {'Range': f'bytes={downloaded_bytes}-'}
        else:
            downloaded_bytes = 0
            headers = {}
        
        # Resume download
        response = requests.get(url, headers=headers, stream=True)
        # ... implementation
```

**Resume Metadata** (JSON):
```json
{
  "url": "https://...",
  "total_size": 6442450944,
  "downloaded_bytes": 3221225472,
  "checksum_partial": "abc123...",
  "timestamp": "2026-01-21T13:00:00"
}
```

**UI Changes**:
- Pause/Resume button on progress page
- "Resume previous download?" dialog on restart
- Progress bar shows resume point

**Implementation Priority**: HIGH (major UX improvement)

---

### 3. Mirror Selection

**Objective**: Allow users to choose preferred mirrors or use automatic selection.

**Technical Requirements**:
- [ ] Mirror speed testing (ping or small file download)
- [ ] Geographic mirror detection (GeoIP or user selection)
- [ ] Mirror preferences storage (config file)
- [ ] Fallback on mirror failure (already implemented in Phase 1)

**Architecture Changes**:
```python
@dataclass
class Mirror:
    url: str
    location: str  # "US-East", "EU-West", "Asia"
    speed_ms: Optional[int] = None  # Ping time
    reliability_score: float = 1.0  # 0.0-1.0
    
class MirrorSelector:
    def test_mirror_speed(self, mirror_url: str) -> int:
        """Test mirror response time"""
        start = time.time()
        response = requests.head(mirror_url, timeout=5)
        return int((time.time() - start) * 1000)
    
    def select_best_mirror(self, mirrors: List[str]) -> str:
        """Choose fastest available mirror"""
        results = []
        for mirror in mirrors:
            try:
                speed = self.test_mirror_speed(mirror)
                results.append((mirror, speed))
            except:
                continue
        return min(results, key=lambda x: x[1])[0] if results else mirrors[0]
```

**UI Changes**:
- Mirror selection dropdown on distro page
- "Auto-select fastest" option (default)
- Mirror speed indicator in preferences

**Implementation Priority**: MEDIUM (builds on Phase 1 infrastructure)

---

### 4. Dynamic Distribution Metadata

**Objective**: Load distribution information from external JSON/API instead of hardcoded Python.

**Technical Requirements**:
- [ ] JSON schema for distribution metadata
- [ ] Local JSON file loading
- [ ] Remote API endpoint support (optional)
- [ ] Caching and update mechanism
- [ ] Validation and error handling

**JSON Schema**:
```json
{
  "version": "2.0",
  "last_updated": "2026-01-21",
  "distributions": [
    {
      "id": "ubuntu",
      "name": "Ubuntu Desktop",
      "description": "Popular Linux distribution...",
      "homepage": "https://ubuntu.com",
      "logo_url": "https://...",
      "category": "Desktop",
      "popularity_rank": 1,
      "releases": [
        {
          "version": "24.04 LTS",
          "release_date": "2024-04-25",
          "iso_url": "https://...",
          "sha256": "089c5af0...",
          "size_mb": 5800,
          "mirrors": [
            "https://mirror1.com/...",
            "https://mirror2.com/..."
          ]
        }
      ]
    }
  ]
}
```

**Architecture Changes**:
```python
class DistroManager:
    def __init__(self, source: Optional[str] = None):
        """
        Args:
            source: Path to JSON file or URL to API endpoint
                   If None, uses default embedded data
        """
        self.source = source or self._get_default_source()
        self._load_distros()
    
    def _load_distros(self):
        """Load from JSON file or API"""
        if self.source.startswith('http'):
            data = self._load_from_api()
        else:
            data = self._load_from_file()
        
        self.distros = self._parse_json(data)
    
    def update_metadata(self) -> bool:
        """Update from remote source"""
        # Download latest JSON
        # Validate schema
        # Save to cache
```

**File Locations**:
- Default: `/usr/share/luxusb/distros.json`
- User custom: `~/.config/luxusb/custom_distros.json`
- Cache: `~/.cache/luxusb/distros.json`
- Remote API: `https://api.luxusb.org/v1/distributions` (future)

**UI Changes**:
- "Update distribution list" button in preferences
- "Last updated" timestamp display
- Custom JSON import option

**Implementation Priority**: MEDIUM (improves maintainability)

---

## Implementation Order

### Week 1: Resume Downloads & Mirror Selection

**Days 1-3: Resume Downloads**
1. Implement `download_with_resume()` method
2. Add `.part` file management
3. Create resume metadata system
4. Add pause/resume UI controls
5. Test with large ISOs (5GB+)

**Days 4-5: Mirror Selection**
1. Implement `MirrorSelector` class
2. Add speed testing functionality
3. Update downloader to use selected mirror
4. Add mirror preference UI
5. Test failover scenarios

### Week 2: Multiple ISO & Dynamic Metadata

**Days 1-3: Multiple ISO Support**
1. Design multi-ISO GRUB configuration
2. Update partition layout for multiple ISOs
3. Implement multi-selection UI
4. Add space calculation
5. Test with 2-3 distributions

**Days 4-5: Dynamic Metadata**
1. Design JSON schema
2. Implement JSON loading
3. Add validation
4. Create migration from Python to JSON
5. Add update mechanism

---

## Testing Strategy

### Unit Tests
- [ ] Resume download with various byte ranges
- [ ] Mirror speed testing and selection
- [ ] JSON schema validation
- [ ] Multi-ISO space calculation

### Integration Tests
- [ ] Resume after network interruption
- [ ] Mirror failover during download
- [ ] Multi-ISO GRUB menu generation
- [ ] JSON update workflow

### User Acceptance Tests
- [ ] Install 3 distributions on one USB
- [ ] Resume 5GB ISO download after pause
- [ ] Auto-select fastest mirror
- [ ] Update distro list from JSON

---

## Success Criteria

✅ **Multiple ISO Support**:
- Users can select 2+ distributions
- GRUB menu shows all installed distros
- Each distro boots successfully

✅ **Resume Downloads**:
- Downloads can be paused and resumed
- Partial downloads survive app restart
- Checksums verified after resume

✅ **Mirror Selection**:
- Auto-selection works reliably
- Manual selection available
- Failover to backup mirrors works

✅ **Dynamic Metadata**:
- Distros load from JSON
- Update mechanism works
- Backward compatible with current code

---

## Migration Strategy

### Backward Compatibility

1. **Keep existing `distro_manager.py`** as fallback
2. **Add JSON export** from current Python data
3. **Gradual migration** to JSON-first approach

### User Migration

1. **First launch after Phase 2**: Export current distros to JSON
2. **Subsequent launches**: Load from JSON
3. **Update button**: Fetch latest from remote (future)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Resume fails for some servers | Medium | Detect Range support, fallback to full download |
| Mirror speed test inaccurate | Low | Test with actual file download (1MB chunk) |
| Multi-ISO GRUB complexity | High | Extensive testing with common distros |
| JSON schema changes break loading | Medium | Version field, strict validation |

---

## Dependencies

**New Python Packages**:
- None (uses existing requests, json)

**System Requirements**:
- Same as Phase 1

**Optional**:
- GeoIP library for automatic location detection (future)

---

## Documentation Updates

- [ ] Update USER_GUIDE.md with multi-ISO instructions
- [ ] Document resume functionality
- [ ] Add mirror selection guide
- [ ] JSON schema documentation

---

## Estimated Timeline

- **Week 1**: Resume downloads + mirror selection
- **Week 2**: Multiple ISO + dynamic metadata
- **Testing**: 2-3 days
- **Documentation**: 1-2 days

**Total**: 2-3 weeks for full Phase 2 implementation

---

## Next Steps

1. Review this plan with stakeholders
2. Begin with resume downloads (highest user value)
3. Implement features incrementally
4. Test each feature before moving to next
5. Update documentation continuously

**Ready to begin?** Start with the most impactful feature: **Resume Downloads**
