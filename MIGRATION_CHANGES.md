# Migration to Simplified Execution Mode

## Summary of Changes Needed in main.py

### Current Structure
The current main.py has complex conditional logic checking multiple flags:
- `config.download_only`
- `config.analyze_existing` 
- `config.download_packages`
- `config.download_iflows`
- etc. (22+ flags)

### New Structure
Simplified to check just one flag:
- `config.execution_mode` (FULL or REPORT_ONLY)

---

## Key Changes Required

### 1. Remove Legacy Mode Checks

**OLD CODE (Lines ~145-175):**
```python
# Check execution mode
if config.analyze_existing:
    logger.info("ANALYZE_EXISTING MODE - Loading existing data")
    # ... load existing JSON files
elif config.download_only:
    # ... download logic
else:
    # ... normal flow
```

**NEW CODE:**
```python
# Check execution mode
if config.execution_mode == "REPORT_ONLY":
    logger.info("REPORT_ONLY MODE - Generating reports only")
    # Skip all downloads, go directly to report generation
    # Use config.report_db_path for database
elif config.execution_mode == "FULL":
    logger.info("FULL MODE - Complete pipeline")
    # Run all downloads/analysis (no conditionals needed)
    # All flags are already TRUE in config.py
```

### 2. Simplify Download Conditionals

**OLD CODE (throughout):**
```python
if config.download_packages and (args.api == 'packages' or not args.api):
    # download packages
elif not config.download_packages:
    logger.info("Packages download disabled (DOWNLOAD_PACKAGES=false)")
```

**NEW CODE:**
```python
# In FULL mode, all downloads enabled (no conditionals)
if not args.api or args.api == 'packages':
    # download packages (always runs in FULL mode)
```

### 3. Remove "Disabled" Messages

All these messages can be removed:
- "Packages download disabled (DOWNLOAD_PACKAGES=false)"
- "IFlows download disabled (DOWNLOAD_IFLOWS=false)"
- etc.

In FULL mode, everything runs. No need to log what's disabled.

### 4. Simplify Database Phase

**OLD CODE:**
```python
if not args.save_only and not config.download_only:
    # database operations
elif config.download_only:
    logger.info("DOWNLOAD_ONLY mode - Skipping database operations")
```

**NEW CODE:**
```python
# In FULL mode, always do database operations (no conditional)
# REPORT_ONLY mode skips this entire section
if config.execution_mode == "FULL":
    # database operations (always runs)
```

### 5. Remove Cleanup Logic

**OLD CODE (Line ~143):**
```python
# Cleanup old runs if configured
if config.keep_runs > 0:
    logger.info(f"Cleaning up old runs (keeping last {config.keep_runs})...")
    config.cleanup_old_runs(config.keep_runs)
```

**NEW CODE:**
```python
# Removed - users manage runs manually
```

---

## Implementation Plan

### Phase 1: Update Execution Mode Logic
1. Replace `analyze_existing` check with `execution_mode == "REPORT_ONLY"`
2. Remove `download_only` check
3. Add REPORT_ONLY mode handler (early exit to report generation)

### Phase 2: Simplify Download Section
1. Remove all individual download flag conditionals
2. Remove "disabled" log messages
3. Keep only API-specific filtering (for --api argument)

### Phase 3: Simplify Database Section
1. Remove `save_only` and `download_only` conditionals
2. Always run database operations in FULL mode

### Phase 4: Clean Up
1. Remove `cleanup_old_runs` call
2. Remove any remaining legacy flag references

---

## Testing Required

After changes:
1. Test FULL mode: `python main.py`
   - Should download everything
   - Should create database
   - Should not skip anything

2. Test REPORT_ONLY mode: 
   ```
   EXECUTION_MODE=REPORT_ONLY
   REPORT_DB_PATH=runs/Trial/20260307_164253/ci_analyzer_Trial_20260307_164253.db
   ```
   - Should skip all downloads
   - Should only generate reports (when implemented)

---

## Notes

- The actual report generation is not yet implemented
- This migration focuses on download/analysis pipeline
- Report generation will be added separately