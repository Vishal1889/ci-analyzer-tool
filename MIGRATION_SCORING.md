# Migration Complexity Index (MCI) — Scoring Methodology

> **Version**: 1.0  
> **Applies to**: NEO to CF Migration Assessment Report  
> **Branch**: `feature/migration-complexity-scoring`

---

## Overview

The **Migration Complexity Index (MCI)** is a score from **0 to 100** that measures how complex a NEO → Cloud Foundry (CF) migration will be for a given SAP Cloud Integration tenant or package.

- **0** = Very simple migration, minimal effort
- **100** = Highly complex migration, significant rework required

The score is computed per-package and then consolidated into an overall tenant score.

### Complexity Tag Thresholds

| Score Range | Tag | Meaning |
|-------------|-----|---------|
| 0 – 25 | 🟢 **Low** | Straightforward migration, mostly configuration changes |
| 26 – 50 | 🟡 **Medium** | Moderate effort, planned migration with testing required |
| 51 – 75 | 🟠 **High** | Significant effort, redesign areas identified |
| 76 – 100 | 🔴 **Critical** | Major rework required, high-risk migration |

---

## Score Components

The total score is built from **6 rules**, each contributing a maximum number of points:

| Rule | Factor | Max Points | Type |
|------|--------|-----------|------|
| Rule 1a | Custom Package Ratio | 10 | Planning scope |
| Rule 1b | Standard Package Version Currency | 10 | Planning scope |
| Rule 2 | Artifact Sync Consistency | 15 | Operational quality |
| Rule 3 | Object Complexity | 10 | Testing effort indicator |
| Rule 4 | Environment Variable Usage | 25 | 🔴 Compatibility blocker |
| Rule 5 | Connected Systems & Adapter Diversity | 20 | Migration connectivity work |
| Rule 6 | Certificate-to-User Mappings | 10 | 🔴 Compatibility blocker |
| | **Total** | **100** | |

Rules 4 and 6 carry the highest weight because they represent **CF compatibility blockers** — patterns that are simply not supported in CF and require mandatory redesign regardless of the number of objects.

---

## Rule 1 — Package Composition & Version Correctness (20 pts total)

### Rule 1a — Custom Package Ratio (10 pts)

**Purpose**: The higher the proportion of custom-built packages, the more code analysis, testing, and potential refactoring is needed. Standard SAP packages are managed by SAP and have known migration paths.

**Formula**:
```
score_1a = (custom_package_count / total_package_count) × 10
```

**Package type classification** (from `package` DB table):

| Condition | Type |
|-----------|------|
| `Mode = 'READ_ONLY'` | Standard (Configure-Only) |
| `Mode != 'READ_ONLY'` AND (`PartnerContent = 1` OR `Vendor LIKE '%sap%'`) | Standard (Editable) |
| `Mode != 'READ_ONLY'` AND NOT PartnerContent AND NOT SAP Vendor | **Custom** |

**Example**:
```
Tenant has 20 packages:
  - 5 Standard (Configure-Only)
  - 7 Standard (Editable)
  - 8 Custom

score_1a = (8 / 20) × 10 = 4.0 pts
```

---

### Rule 1b — Standard Package Version Currency (10 pts)

**Purpose**: If a standard package is already on the latest SAP version (matches Discover version), migration has no version impact for that package. Outdated standard packages need to be updated as part of the migration, adding effort.

**Data source**: `package_discover_version` table (populated only if `DOWNLOAD_DISCOVER_VERSIONS=true`)

**Formula**:
```
score_1b = (outdated_standard_count / total_standard_count) × 10
```

Where `outdated` means `design_version ≠ discover_version`.

**If Discover data is NOT available**: score_1b = **5.0** (neutral mid-point — not penalised for missing data, but no credit either)

**Example**:
```
12 standard packages total (Configure-Only + Editable combined):
  - 9 on latest Discover version  →  up-to-date
  - 3 outdated

score_1b = (3 / 12) × 10 = 2.5 pts

(A fully up-to-date standard landscape = 0 pts for this rule)
```

---

## Rule 2 — Artifact Sync Consistency (15 pts)

**Purpose**: Measures how well-maintained the tenant's runtime is. Artifacts that are undeployed or out-of-sync represent an unknown baseline — you can't reliably test migration if the current state isn't clean.

**Applies to**: All 4 artifact types — IFlows, Script Collections, Message Mappings, Value Mappings

**Sync Status Weights**:

| Status | Weight | Reason |
|--------|--------|--------|
| **Not Deployed** | 1.0 | No runtime baseline at all — highest risk |
| **Out of Sync** | 0.8 | Design changed after last deployment — regression risk |
| **In Sync** | 0.0 | Clean baseline — no complexity contribution |

**Formula**:
```
weighted_unsync = (not_deployed_count × 1.0) + (out_of_sync_count × 0.8)
score_2 = (weighted_unsync / total_artifacts) × 15
```

**Example**:
```
Package has 20 artifacts total:
  - 12 In Sync
  - 5 Out of Sync
  - 3 Not Deployed

weighted_unsync = (3 × 1.0) + (5 × 0.8) = 3.0 + 4.0 = 7.0
score_2 = (7.0 / 20) × 15 = 5.25 pts

(Fully synced package = 0 pts for this rule)
```

---

## Rule 3 — Object Complexity (10 pts)

**Purpose**: Indicates the testing scope and effort. With automatic conversion tools available, object complexity does not block the migration itself — but a complex IFlow with many steps and heavy components (scripts, XSLT) will require more thorough testing.

**Data source**: `bpmn_activity` table — columns `activityType`, `subActivityType`, `iflowId`

### IFlow Step Complexity Weights

Not all steps are equally complex. Heavy steps (custom code, XML transforms) carry more weight:

| `subActivityType` | Weight | Reason |
|-------------------|--------|--------|
| `GroovyScript` | **3** | Custom code — needs code review and testing |
| `XSLT` | **3** | XML transformation — expertise required, verify compatibility |
| `MessageMapping` | **2** | Graphical mapping — usually portable, but test edge cases |
| `exclusiveGateway` | **1.5** | Routing — straightforward but conditional logic needs verification |
| `parallelGateway` | **1.5** | Parallel split/join — review for timing differences |
| All others | **1** | Standard steps — typically auto-convert cleanly |

**Per-IFlow weighted step score**:
```
iflow_weighted_score = SUM(weight for each activity in the IFlow)
```

**Package aggregation**:
```
avg_iflow_score = AVERAGE(iflow_weighted_score for all IFlows in package)
score_3 = min(10, avg_iflow_score / 3.0)
```

The divisor `3.0` is the baseline — an IFlow averaging 3 weighted points per step is considered moderately complex (score = 10/10). Simpler IFlows score below 10, more complex ones are capped at 10.

**Example**:
```
Package has 3 IFlows:

IFlow A (10 steps):
  - 2 GroovyScript × 3 = 6
  - 1 MessageMapping × 2 = 2
  - 7 ContentModifier × 1 = 7
  → weighted score = 15

IFlow B (5 steps):
  - 1 XSLT × 3 = 3
  - 4 ContentModifier × 1 = 4
  → weighted score = 7

IFlow C (3 steps):
  - 3 ContentModifier × 1 = 3
  → weighted score = 3

avg_iflow_score = (15 + 7 + 3) / 3 = 8.33
score_3 = min(10, 8.33 / 3.0) = min(10, 2.78) = 2.78 pts

(Very heavy IFlows with many scripts/XSLT would approach 10 pts)
```

**Note**: Rule 3 also flags presence of `bpmn_timer` entries — IFlows with timers are annotated separately as timers behave differently between NEO and CF scheduling mechanisms.

---

## Rule 4 — Environment Variable Usage (25 pts) 🔴 Blocker

**Purpose**: HC_ environment variables are a NEO-specific primitive for externalising configuration. **They are not supported in CF**. Any script (Groovy, JavaScript) or XSLT file that reads HC_ variables must be redesigned to use CF's externalized parameters or secure parameters mechanism. This is mandatory rework, not optional testing.

**Data source**: `environment_variable_check` table — `fileName`, `fileType`, `envVariableCount`

**File type weights** (XSLT is harder to adapt than script):

| `fileType` | Weight |
|------------|--------|
| `xslt` | **1.5** |
| `groovyScript` | **1.0** |
| `javascript` | **1.0** |

**Formula**:
```
weighted_file_count = SUM(weight per file using HC_ vars in the package)
score_4 = min(25, weighted_file_count / BASELINE × 25)
```

Where `BASELINE = 10.0` — a package with 10+ weighted files using HC_ variables scores the maximum 25 pts.

**Example A — High env variable usage**:
```
Package has these files using HC_ vars:
  - 3 XSLT files   → 3 × 1.5 = 4.5
  - 6 Groovy files → 6 × 1.0 = 6.0
  - 2 JS files     → 2 × 1.0 = 2.0
  → weighted_file_count = 12.5

score_4 = min(25, (12.5 / 10.0) × 25) = min(25, 31.25) = 25.0 pts (capped at max)
```

**Example B — Low env variable usage**:
```
Package has:
  - 1 XSLT file    → 1 × 1.5 = 1.5
  - 2 Groovy files → 2 × 1.0 = 2.0
  → weighted_file_count = 3.5

score_4 = min(25, (3.5 / 10.0) × 25) = min(25, 8.75) = 8.75 pts
```

**Example C — No env variable usage**:
```
score_4 = 0 pts  →  no redesign needed for this rule
```

---

## Rule 5 — Connected Systems & Adapter Diversity (20 pts total)

**Purpose**: More connected systems = more endpoints to re-configure in CF (new credentials, firewall rules, adapter configs). Crucially, the *type* of adapter matters more than raw count — proprietary/on-premise protocol adapters (RFC, IDoc, JDBC) are harder to migrate than standard internet protocols (HTTP, SFTP).

**Data source**: `bpmn_channel` table — `componentType`, `address`, `system`, `iflowId`

---

### Rule 5a — System Count (10 pts)

**Formula** (piecewise linear):
```
systems ≤ 10:   score = (systems / 10) × 4          → max 4.0 pts
systems ≤ 30:   score = 4 + ((systems - 10) / 20) × 4   → max 8.0 pts
systems ≤ 60:   score = 8 + ((systems - 30) / 30) × 2   → max 10.0 pts
systems > 60:   score = 10 pts (maximum)
```

| Systems | Score |
|---------|-------|
| 5 | 2.0 |
| 15 | 5.0 |
| 30 | 8.0 |
| 50 | 9.3 |
| 60+ | 10.0 |

---

### Rule 5b — Adapter Complexity Tier (10 pts)

Adapters are categorised into 3 tiers based on migration complexity:

| Tier | Adapters | Weight |
|------|----------|--------|
| 🔴 **Complex** | RFC, IDoc, JDBC, JMS, AMQP, AS2, XI, SFTP (outbound) | **3** |
| 🟡 **Moderate** | SOAP, Mail, FTP, SuccessFactors, Ariba | **2** |
| 🟢 **Simple** | HTTP, HTTPS, OData, REST, ProcessDirect | **1** |

**Formula**:
```
adapter_weighted_score = SUM(adapter_count × tier_weight for each adapter type)
score_5b = min(10, adapter_weighted_score / BASELINE × 10)
```

Where `BASELINE = 50` — a tenant with 50 weighted adapter instances scores maximum.

**Example — Many systems but mostly HTTP**:
```
Tenant has:
  - 80 HTTP/HTTPS adapters  → 80 × 1 = 80
  - 5 SOAP adapters         → 5 × 2 = 10
  - 2 RFC adapters          → 2 × 3 = 6
  → adapter_weighted_score = 96

score_5b = min(10, (96/50) × 10) = 10 pts (capped — but see below)

BUT: 80 of those are simple HTTP → adapter diversity is low.
```

> **Design note**: The tier weights naturally produce a lower score per adapter for simple types. A landscape with 80 HTTP adapters vs 80 RFC adapters scores very differently on the weighted sum even at the same count.

**Combined Rule 5 score**:
```
score_5 = score_5a + score_5b   (max 20 pts)
```

---

## Rule 6 — Certificate-to-User Mappings (10 pts) 🔴 Blocker

**Purpose**: Certificate-to-User mappings are a NEO-exclusive security feature that maps inbound client certificates to SAP user accounts. **This feature does not exist in CF**. Any tenant using this pattern must redesign their inbound authentication — typically migrating to OAuth 2.0 client credentials or basic authentication with service accounts. This is a mandatory blocker.

**Data source**: `security_certificate_user_mapping` table

**Formula**:
```
score_6 = min(10, cert_mapping_count × 0.5)
```

This scales rather than being purely binary — 2 mappings is very different work from 50 mappings.

| Mappings | Score |
|----------|-------|
| 0 | 0.0 pts — no redesign needed |
| 1–2 | 0.5–1.0 pts — minor effort |
| 5 | 2.5 pts — moderate |
| 10 | 5.0 pts — significant |
| 20+ | 10.0 pts (max) — major redesign |

---

## Per-Package Score Assembly

### Custom Package

All 6 rules apply (Rules 5 and 6 use the package's proportional share of tenant-wide values):

```
package_score = rule1a + rule1b + rule2 + rule3 + rule4 + rule5_pkg + rule6_pkg

rule5_pkg = score_5 × (iflows_in_package / total_iflows_in_tenant)
rule6_pkg = score_6 (same for all packages — it's a tenant-wide flag)
```

### Standard Package (Configure-Only or Editable)

Rules 1b and 2 are the primary drivers. Object complexity, env variables, and systems are less relevant as SAP owns the content:

```
package_score = (rule1b × 2.0) + (rule2 × 1.5)
             normalized to 0–100 scale
```

> Standard packages on the latest version with fully synced artifacts → score near 0 (🟢 Low complexity).

---

## Consolidated Tenant Score

```
custom_avg   = AVERAGE(score for all Custom packages)
standard_avg = AVERAGE(score for all Standard packages)

overall_mci  = (custom_avg × custom_weight) + (standard_avg × standard_weight)

Where:
  custom_weight   = custom_count / total_packages
  standard_weight = standard_count / total_packages
```

This weighted average means a tenant dominated by custom packages will reflect higher overall complexity.

---

## Full Worked Example

**Tenant: "ACME_NEO"**

| | Value |
|---|---|
| Total packages | 15 |
| Custom packages | 6 |
| Standard (Editable) | 4 |
| Standard (Configure-Only) | 5 |
| Standard packages on Discover latest | 7 of 9 |
| Total artifacts | 120 |
| Not Deployed | 10 |
| Out of Sync | 15 |
| Total IFlows | 40 |
| Avg IFlow weighted step score | 6.0 |
| Files using HC_ env vars | 8 Groovy + 2 XSLT |
| Unique systems | 25 |
| RFC adapters | 8 |
| HTTP/HTTPS adapters | 30 |
| SOAP adapters | 6 |
| Certificate-to-User mappings | 12 |

### Rule 1a (Custom Ratio):
```
score_1a = (6 / 15) × 10 = 4.0 pts
```

### Rule 1b (Version Currency):
```
outdated_standard = 9 - 7 = 2
score_1b = (2 / 9) × 10 = 2.2 pts
```

### Rule 2 (Sync Consistency):
```
weighted_unsync = (10 × 1.0) + (15 × 0.8) = 10 + 12 = 22
score_2 = (22 / 120) × 15 = 2.75 pts
```

### Rule 3 (Object Complexity):
```
avg_iflow_weighted = 6.0
score_3 = min(10, 6.0 / 3.0) = min(10, 2.0) = 2.0 pts
```

### Rule 4 (Env Variables):
```
weighted_files = (8 × 1.0) + (2 × 1.5) = 8 + 3 = 11
score_4 = min(25, (11 / 10) × 25) = min(25, 27.5) = 25.0 pts  ← blocker maxed out
```

### Rule 5a (System Count — 25 systems):
```
score_5a = 4 + ((25 - 10) / 20) × 4 = 4 + (15/20) × 4 = 4 + 3.0 = 7.0 pts
```

### Rule 5b (Adapter Tier):
```
weighted = (8 × 3) + (30 × 1) + (6 × 2) = 24 + 30 + 12 = 66
score_5b = min(10, (66/50) × 10) = min(10, 13.2) = 10.0 pts
score_5 = 7.0 + 10.0 = 17.0 pts
```

### Rule 6 (Cert Mappings — 12 mappings):
```
score_6 = min(10, 12 × 0.5) = min(10, 6.0) = 6.0 pts  ← significant
```

### Total MCI:
```
MCI = 4.0 + 2.2 + 2.75 + 2.0 + 25.0 + 17.0 + 6.0 = 58.95 → 59

Complexity Tag: 🟠 High (51–75)
```

**Interpretation**: The tenant scores **High complexity** primarily driven by:
1. Rule 4 (env variables) — maxed at 25 pts — **mandatory redesign** of 10 files
2. Rule 5 (systems/adapters) — 17 pts — significant connectivity re-wiring, especially 8 RFC adapters
3. Rule 6 (cert mappings) — 6 pts — 12 mappings need authentication redesign

Rules 1–3 contribute relatively little (10.95 pts combined) which is expected for a moderately well-maintained tenant.

---

## Pre-Computed Table Structure

Scores are computed once after data ingestion and stored in `package_migration_score`:

```sql
CREATE TABLE package_migration_score (
    tenant_id        TEXT,
    package_id       TEXT,
    package_name     TEXT,
    package_type     TEXT,   -- Custom / Standard (Editable) / Standard (Configure-Only)
    rule1a_score     REAL,
    rule1b_score     REAL,
    rule2_score      REAL,
    rule3_score      REAL,
    rule4_score      REAL,
    rule5_score      REAL,
    rule6_score      REAL,
    total_score      REAL,
    complexity_tag   TEXT,   -- Low / Medium / High / Critical
    computed_at      TEXT
)
```

The report generator reads from this table with a single query — no runtime aggregation.

---

## Configuration Constants

All thresholds are defined as named constants in `migration_score_calculator.py` so they can be tuned without touching scoring logic:

```python
RULE4_BASELINE = 10.0      # Weighted files count for max env var score
RULE5B_BASELINE = 50.0     # Weighted adapter count for max adapter score
RULE6_MULTIPLIER = 0.5     # Points per cert mapping
RULE3_STEP_BASELINE = 3.0  # Avg weighted steps/IFlow for max object complexity

COMPLEXITY_THRESHOLDS = {
    'Low':      (0, 25),
    'Medium':   (26, 50),
    'High':     (51, 75),
    'Critical': (76, 100)
}

ADAPTER_TIER_WEIGHTS = {
    # Complex (on-prem / proprietary)
    'RFC': 3, 'IDoc': 3, 'JDBC': 3, 'JMS': 3,
    'AMQP': 3, 'AS2': 3, 'XI': 3,
    # Moderate
    'SOAP': 2, 'Mail': 2, 'FTP': 2,
    'SuccessFactors': 2, 'Ariba': 2,
    # Simple (default for unknowns = 1)
    'HTTP': 1, 'HTTPS': 1, 'OData': 1, 'REST': 1
}

ACTIVITY_WEIGHTS = {
    'GroovyScript': 3,
    'XSLT': 3,
    'MessageMapping': 2,
    'exclusiveGateway': 1.5,
    'parallelGateway': 1.5,
}
ACTIVITY_DEFAULT_WEIGHT = 1.0
```

---

*Document maintained alongside `feature/migration-complexity-scoring` branch.*