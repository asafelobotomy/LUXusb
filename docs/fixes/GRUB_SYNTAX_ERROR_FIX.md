# GRUB Syntax Error Fix

**Date**: 2026-01-28  
**Issue**: Boot failure with GRUB script syntax errors

## Problem

When booting from USB, multiple GRUB syntax errors were displayed:
```
error: script/execute.c:grub_script_return:230:not in function body.
error: script/lexer.c:grub_script_yyerror:352:syntax error.
error: script/lexer.c:grub_script_yyerror:352:incorrect command.
```

These errors prevented the system from booting Linux distributions.

## Root Cause

The generated GRUB configuration used `return` statements inside `menuentry` blocks. In GRUB scripting:
- `return` is **only valid inside function definitions** (created with `function` keyword)
- `return` is **not valid inside menuentry blocks**

Example of problematic code:
```grub
menuentry 'Ubuntu 24.04' {
    if [ "$root" = "" ]; then
        echo "ERROR: Partition not found"
        read
        return    # ❌ SYNTAX ERROR - not in function body
    fi
}
```

## Solution

**Removed all `return` statements** from menuentry blocks and restructured the logic to use proper conditional nesting:

```grub
menuentry 'Ubuntu 24.04' {
    if [ "$root" = "" ]; then
        echo "ERROR: Partition not found"
        read
    else
        # Continue with boot process only if partition found
        echo "Found partition: $root"
        loopback loop "$isopath"
        # ... boot commands ...
    fi
}
```

### Changes Made

Modified [`luxusb/utils/grub_installer.py`](../../luxusb/utils/grub_installer.py):

1. **Line ~383-405**: Removed `return` from partition search error block in `_generate_distro_entries()`
   - Used `else` block to only proceed if partition found

2. **Line ~393-407**: Removed `return` from ISO file verification error block
   - Nested ISO loading inside `else` block to ensure file exists

3. **Line ~558-606**: Removed `return` from custom ISO error blocks
   - Applied same conditional nesting pattern

### Error Block Pattern (Before → After)

**Before** (❌ Syntax Error):
```grub
if [ "$root" = "" ]; then
    echo "ERROR: Partition not found"
    read
    return    # ❌ Invalid in menuentry
fi
# Code continues even if error occurred
```

**After** (✅ Correct):
```grub
if [ "$root" = "" ]; then
    echo "ERROR: Partition not found"
    read
else
    # Code only runs if no error
    echo "Found partition: $root"
    # ... continue boot process ...
fi
```

## Testing

To regenerate GRUB configuration with fixes:

```bash
# Rebuild USB drive from scratch
sudo python3 -m luxusb

# Or manually refresh GRUB config on existing USB
sudo python3 -c "
from luxusb.utils.grub_installer import GRUBInstaller
from pathlib import Path

installer = GRUBInstaller('/dev/sdX', Path('/mnt/efi'))
installer.generate_config_from_isos([], [])
"
```

## Files Modified

- [`luxusb/utils/grub_installer.py`](../../luxusb/utils/grub_installer.py) - Main fix
- No changes needed to `grub_refresher.py` (uses GRUBInstaller)

## Verification

The fix ensures:
1. ✅ No `return` statements exist inside any `menuentry` blocks
2. ✅ Error conditions prevent subsequent code execution via `else` blocks
3. ✅ User sees clear error messages before returning to menu
4. ✅ GRUB syntax validation passes

## Additional Notes

- The `read` command pauses execution and waits for user keypress
- After `read` completes, GRUB automatically returns to the menu when the menuentry block ends
- No explicit `return` is needed or allowed in menuentries
