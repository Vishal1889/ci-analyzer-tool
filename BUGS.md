# Bug Tracker

Findings from code review. Work through in order — check off each one when fixed.

---

## 🔴 Critical — Crashes / Total Data Loss

- [x] **B01** `main.py` ~565 — Hard subscript `download_results['script_collections']['items']` inside broad try/except; KeyError silently zeros all IFLW tables
- [x] **B02** `main.py` ~1377 — `--save-only` + `CLEANUP_DOWNLOADS=true` deletes the downloads folder after skipping DB import, leaving the run with nothing
- [x] **B03** `neo_to_cf_migration.py` ~1243 — Negative UTC offset (e.g. `-05:00`) not stripped from cert timestamp; `datetime.now()` (naive) vs aware datetime → `TypeError`; all cert statuses show `Unknown`
- [x] **B04** `oauth_client.py` ~100 — Missing `access_token` in OAuth response returns `None` silently; every API call sends `Authorization: Bearer None`
- [x] **B05** `partner_directory_downloader.py` ~168 — `item.get('ContentType', 'unknown')` returns `None` when key exists with JSON `null` value; `.lower()` on `None` → `AttributeError` crash
- [x] **B06** `security_downloader.py` ~303 — Uses `not_valid_before_utc` / `not_valid_after_utc` (requires cryptography ≥ 42.0); older installs → `AttributeError` for every cert, all cert fields stored as `null`

---

## 🟠 High — Wrong Data / Silent Data Loss

- [x] **B07** `neo_to_cf_migration.py` ~383 — Dashboard donut chart queries `message_mapping.Version` and `environment_variable_check.parentName` directly, bypassing `_mm_source`/`_evc_pname_subq` guards; donut blank when tenant has 0 message mappings
- [x] **B08** `neo_to_cf_migration.py` ~661 — Draft artifacts query references `message_mapping.PackageId/.Name/.Version` directly (not via `_mm_source`); when `_mm_has_schema=False`, all packages show "no draft artifacts"
- [x] **B09** `neo_to_cf_migration.py` ~637, 912 — HC_ file detail queries in `_compute_package_readiness` and `_generate_version_deployment` bypass `_evc_has_schema`; readiness colour correct but popover details always empty
- [x] **B10** `neo_to_cf_migration.py` ~1148, 1181 — `unique_vars_count` computed but never returned; `'total_variables'` key returns file count (row count from JOIN), not unique variable count
- [x] **B11** `neo_to_cf_migration.py` ~366, 519 — `COUNT(DISTINCT sc.Name)` for script collections; should be `sc.Id`; same-name collections undercounted
- [x] **B12** `neo_to_cf_migration.py` ~148 — `dict.get('custom_packages', 0)` returns `None` when SQLite aggregate returns SQL NULL (0-row package table); downstream numeric operations produce `None` in report
- [x] **B13** `neo_to_cf_migration.py` ~477 — Fallback version comparison query filters `WHERE Vendor IS NOT NULL AND Vendor != ''`; custom packages with no Vendor silently excluded
- [x] **B14** `neo_to_cf_migration.py` ~776 — `p.ModifiedDate < date('now', '-180 days')` is lexicographic if column stores OData `/Date(ms)/` strings; every package labelled `Outdated`
- [x] **B15** `oauth_client.py` ~103 — `expires_in - 300` goes negative if token lifetime < 300 s; expiry set in the past, token refreshed on every API call
- [x] **B16** `artifact_zip_downloader.py` ~474 — Mid-stream connection failure leaves truncated ZIP on disk; next extraction raises `BadZipFile` with no retry
- [x] **B17** `base_downloader.py` ~173 — `_fetch_all_pages` catches `RequestException` and returns partial page accumulation as if complete; caller has no way to know data is incomplete
- [x] **B18** `environment_variable_scanner.py` ~96 — `files_scanned` stat equals `files_with_vars`; `None` results (zero-var files) filtered before stats loop; total files actually read is never tracked
- [ ] **B19** `iflw_timer_extractor.py` ~203 — `_extract_scheduled_channels` passes `configurations` (possibly `None`) to resolver without guard; `None` dict lookup → `TypeError`
- [x] **B20** `db_manager.py` ~258 — INSERT uses unquoted column names; CREATE TABLE uses quoted ones; any OData field that is a SQLite reserved word → `OperationalError`, table silently empty

---

## 🟡 Medium — UX / Incorrect Output

- [x] **B21** `neo_cf_formatter.py` ~45 — All assets (Bootstrap, Chart.js, jQuery, DataTables) loaded from CDN; on air-gapped SAP customer networks the report renders as unstyled text with no charts or interactive tables
- [x] **B22** `neo_cf_formatter.py` multiple — Package names, artifact names, URLs, error messages interpolated into `<td>` cells without HTML escaping; SAP names with `&` (e.g. "SAP Ariba & Procurement") produce malformed HTML
- [x] **B23** `neo_cf_formatter.py` ~974, 1153 — `checks_json` data attribute escapes `"` but not `&`; `&` in readiness check detail text produces malformed attribute; browser decodes HTML entities before jQuery reads them, corrupting JSON values
- [x] **B24** `neo_cf_formatter.py` ~1543, 1631 — X.509 DN strings in `title` attributes not HTML-escaped; DN with `&` (e.g. `O=AT&T`) or `"` breaks the attribute
- [x] **B25** `neo_cf_formatter.py` ~2069 — Iflow usage modal splits comma-delimited list on `,`; iflow/package names containing commas produce wrong entries in the modal
- [x] **B26** `neo_cf_formatter.py` ~828, 2246 — `_donut_data` set as side-effect in `_generate_tab_executive_summary`, consumed in `_generate_javascript`; relies on f-string left-to-right evaluation order; fragile if call order ever changes
- [x] **B27** `neo_cf_formatter.py` ~1948 — Only `\` and `"` escaped in JS tenant ID string; newline or `\r` in tenant ID produces a JS syntax error that disables all interactive features
- [x] **B28** `main.py` ~210, 1368 — "not yet implemented" logged immediately after HTML report is successfully written; false alarm for any log monitoring
- [x] **B29** `main.py` ~180 vs 1243 — REPORT_ONLY produces naive ISO timestamp; FULL mode produces timezone-aware timestamp; `fromisoformat` + compare can raise `TypeError`
- [x] **B30** `main.py` ~539 — `--save-only` only gates Phase 2; phases 1.5–1.10 (ZIP extraction, IFLW analysis, env var scan) still run, contradicting the flag's documented purpose *(phases 1.5–1.6 fixed; 1.7–1.10 remain as a known limitation)*
- [x] **B31** `iflw_channel_extractor.py` ~606 — `resolved_value or raw_value` treats empty string as falsy and falls back to raw; an intentionally empty resolved config value is silently replaced
- [x] **B32** `artifact_zip_downloader.py` ~840 — `attempted_path.relative_to(self.download_dir.parent)` inside the error handler; if path is not a subpath, raises `ValueError`, masking the original download error
- [x] **B33** `discover_version_checker.py` ~196 — `_delete_package` failure is logged but function still returns version result; orphaned packages accumulate in the Discover tenant across repeated runs

---

## 🔵 Low — Performance / Latent

- [x] **B34** `db_manager.py` ~284 — Row-by-row `cursor.execute()` in the "bulk insert" loop; `executemany()` would be significantly faster for large tables
- [x] **B35** `configuration_downloader.py` ~232 — `_get_package_id_for_iflow` opens and JSON-decodes `iflows.json` on every call; with 500 iflows at 10 workers = 500 redundant file reads under parallel I/O
- [x] **B36** `filename_sanitizer.py` ~44 — `max_stem` can go negative if `max_length` is small; `stem[:-N]` with negative N removes from the end rather than clamping, producing filename longer than `max_length`
- [x] **B37** `ui.py` ~821 — `_browse_db_file` uses `Path("runs")` relative to process CWD; in PyInstaller build, Browse button for `REPORT_DB_PATH` opens at wrong location
- [x] **B38** `ui.py` ~790 — Stop on Windows produces exit code 1 (not 130); always hits the `else` branch and shows red "Process exited with code 1" instead of "Stopped by user"
- [x] **B39** `ui.py` ~701 — `_save_env` writes values unquoted; values with leading/trailing spaces silently trimmed on reload; values with ` #` truncated at inline comment marker
