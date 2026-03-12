# Migration Readiness Score (MRS) — Methodology

## Overview

The **Migration Readiness Score (MRS)** is a per-package score from **0 to 100** that indicates how ready a package is for migration from SAP Integration Suite **NEO** to **Cloud Foundry (CF)**.

> **Higher score = More ready for migration**
>
> A score of 100 means the package has no detected migration complexity and should migrate with minimal effort.  
> A score of 0 means the package has maximum detected complexity and requires significant migration planning.

The MRS is computed as the **inverse** of an underlying complexity measurement:

```
MRS = 100 − (sum of complexity penalty points across 6 rules)
```

---

## Readiness Tags

| MRS Range | Tag            | Meaning                                                   |
|-----------|----------------|-----------------------------------------------------------|
| 76 – 100  | 🟢 Ready        | Low complexity — migrate with standard procedures         |
| 51 – 75   | 🟡 Mostly Ready | Moderate complexity — some configuration review needed    |
| 26 – 50   | 🟠 Needs Work   | High complexity — plan adapters, mappings & env variables |
| 0  – 25   | 🔴 Not Ready    | Critical complexity — requires detailed migration project |

---

## The 6 Rules (Penalty Points)

Each rule contributes **penalty points** (higher penalty = lower readiness). The total penalty is capped at 100.

### Rule 1a — Custom Package Ratio (max 10 pts penalty)

Measures what fraction of the tenant's packages are **custom-built** (not SAP/partner content).  
Custom packages require code review, testing, and rework during migration; standard SAP packages auto-migrate.

```
penalty = (custom_packages / total_packages) × 10
```

- All packages custom → 10 pts penalty (hardest migration)
- All packages standard → 0 pts penalty (easiest migration)

---

### Rule 1b — Standard Package Version Currency (max 10 pts penalty)

Applies to **Standard (SAP/Partner)** packages only.  
If a standard package is behind the latest version on SAP Discover, it should be updated before migration.

```
penalty = 10   if package is outdated vs Discover
penalty = 0    if package is up-to-date
penalty = 5    if Discover data unavailable (neutral)
```

For custom packages: **0 pts** (not applicable — no Discover version).

---

### Rule 2 — Artifact Sync Consistency (max 15 pts penalty)

Measures the ratio of **undeployed** and **out-of-sync** artifacts within the package.  
Migrating a package where design ≠ runtime means extra reconciliation work.

```
weighted_bad = (not_deployed × 1.0) + (out_of_sync × 0.8)
penalty = (weighted_bad / total_artifacts) × 15
```

- All artifacts in sync → 0 pts (fully ready)
- All artifacts not deployed or out of sync → 15 pts (needs reconciliation before migration)

---

### Rule 3 — Object Complexity (max 10 pts penalty)

Measures the **weighted average step complexity** per IFlow in the package.

Step weights by type:

| Step Type         | Weight | Reason                                   |
|-------------------|--------|------------------------------------------|
| Groovy Script     | 3.0    | Custom code — must be reviewed & tested  |
| XSLT              | 3.0    | XML transforms — expertise required      |
| Message Mapping   | 2.0    | Graphical — portable but needs edge-case testing |
| Exclusive Gateway | 1.5    | Routing logic                            |
| Parallel Gateway  | 1.5    | Parallel split/join                      |
| All other steps   | 1.0    | Standard activities — auto-convert cleanly |

```
avg_weighted_steps = mean(weighted_step_score per IFlow)
penalty = min(10, avg_weighted_steps / 3.0)
```

---

### Rule 4 — Environment Variable Usage (max 25 pts penalty, custom packages only)

Counts **HC_ environment variable** references across scripts and XSLTs in the package.  
HC_ variables are NEO-specific and must be mapped to CF equivalents during migration.

File type weights:

| File Type    | Weight |
|--------------|--------|
| XSLT         | 1.5    |
| Groovy       | 1.0    |
| JavaScript   | 1.0    |

```
weighted_files = Σ (file_count × file_weight)
penalty = min(25, (weighted_files / 10.0) × 25)
```

Only applies to **custom packages**. Standard SAP packages are 0.

---

### Rule 5 — Systems & Adapter Diversity (max 20 pts penalty)

Measures the complexity of external system connectivity that must be reconfigured in CF.

**Rule 5a — Unique system count (max 10 pts):**
```
n = count of distinct systems/addresses (excluding ProcessDirect)

n ≤ 10  → penalty = (n / 10) × 4
n ≤ 30  → penalty = 4 + ((n − 10) / 20) × 4
n ≤ 60  → penalty = 8 + ((n − 30) / 30) × 2
n > 60  → penalty = 10 (capped)
```

**Rule 5b — Adapter tier complexity (max 10 pts):**

| Adapter Type          | Complexity Weight |
|-----------------------|-------------------|
| RFC, IDoc, JDBC, JMS, AMQP, AS2, XI | 3.0 (high) |
| SOAP, Mail, FTP, SuccessFactors, Ariba | 2.0 (moderate) |
| HTTP, HTTPS, OData, REST, ProcessDirect | 1.0 (simple) |

```
adapter_weighted = Σ (adapter_instance_count × tier_weight)
rule5b_penalty = min(10, (adapter_weighted / 50) × 10)
```

**Package-level allocation:** Each package's Rule 5 penalty is proportional to its share of the tenant's total IFlows.

---

### Rule 6 — Certificate-to-User Mappings (max 10 pts penalty)

NEO tenants can have certificate-to-user mappings that do not exist in CF.  
Each mapping represents a manual identity reconfiguration step.

```
penalty = min(10, mapping_count × 0.5)
```

A tenant with 20+ cert-to-user mappings reaches maximum penalty.

---

## Scoring for Standard vs Custom Packages

**Custom packages** use all 6 rules (max 100 pts penalty):
```
raw_penalty = Rule1a + Rule1b + Rule2 + Rule3 + Rule4 + Rule5 + Rule6
total_penalty = min(100, raw_penalty)
```

**Standard packages** (SAP/Partner content) use a simplified formula since SAP owns the code:
```
raw_penalty = (Rule1b × 2.5) + (Rule2 × 2.0)
total_penalty = min(100, raw_penalty)
```
The primary concern for standard packages is whether they are version-current and properly deployed.

---

## Final MRS Calculation

```
MRS = round(100 − total_penalty)
MRS is clamped to [0, 100]
```

---

## Tenant-Level Summary

The **Overall MRS** is the weighted average of all package readiness scores:

```
overall_mrs = weighted_average(readiness_score per package)
```

Separate averages are also shown for **Custom Packages** and **Standard Packages**.

---

## Worked Example

| Rule | Scenario                                    | Penalty |
|------|---------------------------------------------|---------|
| 1a   | 8 of 20 packages are custom (40%)           | 4.0     |
| 1b   | Package is up-to-date in Discover           | 0.0     |
| 2    | 2 of 10 artifacts not deployed              | 3.0     |
| 3    | Avg IFlow has 2 Groovy + 3 standard steps   | 4.5     |
| 4    | 3 XSLT files use HC_ vars                  | 7.5     |
| 5    | 25 systems, mix of SOAP/HTTP adapters       | 6.0     |
| 6    | 4 certificate-to-user mappings              | 2.0     |
| **Total penalty** |                                | **27.0** |
| **MRS** | 100 − 27 = **73** → 🟡 Mostly Ready   |         |

---

## Database Storage

Results are stored in the `package_migration_score` table after PHASE 2.3:

| Column          | Description                               |
|-----------------|-------------------------------------------|
| `tenant_id`     | Tenant identifier                         |
| `package_id`    | SAP package ID                            |
| `package_name`  | Human-readable name                       |
| `package_type`  | Custom / Standard (Editable) / Standard (Configure-Only) |
| `rule1a_score`  | Rule 1a complexity penalty (0–10)         |
| `rule1b_score`  | Rule 1b complexity penalty (0–10)         |
| `rule2_score`   | Rule 2 complexity penalty (0–15)          |
| `rule3_score`   | Rule 3 complexity penalty (0–10)          |
| `rule4_score`   | Rule 4 complexity penalty (0–25)          |
| `rule5_score`   | Rule 5 complexity penalty (0–20)          |
| `rule6_score`   | Rule 6 complexity penalty (0–10)          |
| `total_score`   | Sum of all penalties (0–100)              |
| `readiness_score` | Migration Readiness Score = 100 − total_score (0–100) |
| `readiness_tag` | 🟢 Ready / 🟡 Mostly Ready / 🟠 Needs Work / 🔴 Not Ready |
| `computed_at`   | ISO 8601 timestamp of computation         |