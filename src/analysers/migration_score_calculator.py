"""
Migration Complexity Index (MCI) Calculator
Pre-computes per-package migration complexity scores based on 6 rules.
Results are stored in the `package_migration_score` table for fast report generation.

Scoring methodology: see MIGRATION_SCORING.md
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants — adjust thresholds here without touching logic
# ---------------------------------------------------------------------------

RULE4_BASELINE = 10.0       # Weighted files count that yields max env-var score
RULE5B_BASELINE = 50.0      # Weighted adapter instances that yield max adapter score
RULE6_MULTIPLIER = 0.5      # Points added per certificate-to-user mapping
RULE3_STEP_BASELINE = 3.0   # Avg weighted steps/IFlow considered "moderately complex"

COMPLEXITY_THRESHOLDS = {
    'Low':      (0,  25),
    'Medium':   (26, 50),
    'High':     (51, 75),
    'Critical': (76, 100),
}

# adapter componentType → migration complexity weight
ADAPTER_TIER_WEIGHTS: Dict[str, float] = {
    # Complex — on-prem / proprietary protocols (weight 3)
    'RFC':          3.0,
    'IDoc':         3.0,
    'JDBC':         3.0,
    'JMS':          3.0,
    'AMQP':         3.0,
    'AS2':          3.0,
    'XI':           3.0,
    # Moderate — standard enterprise protocols (weight 2)
    'SOAP':         2.0,
    'Mail':         2.0,
    'FTP':          2.0,
    'SuccessFactors': 2.0,
    'Ariba':        2.0,
    # Simple — internet protocols (weight 1)
    'HTTP':         1.0,
    'HTTPS':        1.0,
    'OData':        1.0,
    'REST':         1.0,
    'ProcessDirect': 1.0,
}
ADAPTER_DEFAULT_WEIGHT = 1.5  # unknown adapter types → moderate-ish

# BPMN activity subActivityType → step complexity weight
ACTIVITY_WEIGHTS: Dict[str, float] = {
    'GroovyScript':    3.0,   # Custom code — needs review & testing
    'XSLT':            3.0,   # XML transform — expertise required
    'MessageMapping':  2.0,   # Graphical mapping — portable but test edge cases
    'exclusiveGateway': 1.5,  # Routing logic
    'parallelGateway': 1.5,   # Parallel split/join
}
ACTIVITY_DEFAULT_WEIGHT = 1.0  # standard steps auto-convert cleanly

# File type weights for env variable usage
ENV_VAR_FILE_WEIGHTS: Dict[str, float] = {
    'xslt':         1.5,
    'groovyScript': 1.0,
    'javascript':   1.0,
}
ENV_VAR_DEFAULT_WEIGHT = 1.0


def _complexity_tag(score: float) -> str:
    """Return the complexity tag string for a given MCI score."""
    rounded = round(score)
    for tag, (lo, hi) in COMPLEXITY_THRESHOLDS.items():
        if lo <= rounded <= hi:
            return tag
    return 'Critical'


class MigrationScoreCalculator:
    """
    Computes Migration Complexity Index (MCI) scores for every package in a
    tenant and writes the results to the `package_migration_score` table.

    Call `compute_and_store()` once after all JSON data has been imported.
    The NEO-to-CF report generator then reads from that table instead of
    running many heavy aggregation queries at report time.
    """

    def __init__(self, db_path: str, tenant_id: str):
        self.db_path = Path(db_path)
        self.tenant_id = tenant_id

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def compute_and_store(self) -> Dict[str, Any]:
        """
        Compute MCI scores for all packages and persist to DB.

        Returns:
            dict with summary statistics about the computation run.
        """
        logger.info("=== Migration Complexity Index (MCI) computation started ===")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            self._ensure_table(conn)

            # Delete any previous scores for this tenant (re-run safe)
            conn.execute(
                "DELETE FROM package_migration_score WHERE tenant_id = ?",
                (self.tenant_id,)
            )
            conn.commit()

            # Collect tenant-wide data used by multiple rules
            tenant_ctx = self._build_tenant_context(conn)

            # Get all packages
            packages = self._fetch_packages(conn)
            logger.info(f"  Computing MCI for {len(packages)} packages...")

            rows = []
            for pkg in packages:
                row = self._score_package(conn, pkg, tenant_ctx)
                rows.append(row)
                logger.debug(
                    f"  [{row['complexity_tag']:8s}] {row['package_name'][:50]:50s} "
                    f"MCI={row['total_score']:5.1f}"
                )

            # Bulk insert
            self._insert_scores(conn, rows)
            conn.commit()

            # Summary
            summary = self._build_summary(rows)
            logger.info(
                f"  MCI computation complete: {len(rows)} packages scored | "
                f"Overall tenant MCI = {summary['overall_mci']:.1f} "
                f"({summary['overall_tag']})"
            )
            return summary

        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Table management
    # ------------------------------------------------------------------

    def _ensure_table(self, conn: sqlite3.Connection):
        """Create package_migration_score table if it does not exist."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS package_migration_score (
                tenant_id      TEXT,
                package_id     TEXT,
                package_name   TEXT,
                package_type   TEXT,
                rule1a_score   REAL,
                rule1b_score   REAL,
                rule2_score    REAL,
                rule3_score    REAL,
                rule4_score    REAL,
                rule5_score    REAL,
                rule6_score    REAL,
                total_score    REAL,
                complexity_tag TEXT,
                has_timers     INTEGER,
                computed_at    TEXT
            )
        """)
        conn.commit()

    # ------------------------------------------------------------------
    # Data fetching helpers
    # ------------------------------------------------------------------

    def _fetch_packages(self, conn: sqlite3.Connection) -> List[sqlite3.Row]:
        """Return all packages for the tenant with their type classification."""
        return conn.execute("""
            SELECT
                p.Id        AS package_id,
                p.Name      AS package_name,
                p.Mode      AS mode,
                p.PartnerContent AS partner_content,
                p.Vendor    AS vendor,
                CASE
                    WHEN p.Mode = 'READ_ONLY' THEN 'Standard (Configure-Only)'
                    WHEN p.Mode != 'READ_ONLY'
                         AND (p.PartnerContent = '1'
                              OR LOWER(COALESCE(p.Vendor,'')) LIKE '%sap%')
                        THEN 'Standard (Editable)'
                    ELSE 'Custom'
                END AS package_type
            FROM package p
            WHERE p.tenant_id = ?
            ORDER BY p.Name
        """, (self.tenant_id,)).fetchall()

    def _build_tenant_context(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Collect tenant-wide statistics that are needed by Rules 1, 5, and 6
        so we don't repeat these queries per package.
        """
        ctx: Dict[str, Any] = {}

        # ---- Rule 1a: total + custom package counts ----
        pkg_counts = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE
                    WHEN Mode != 'READ_ONLY'
                         AND (PartnerContent != '1' OR PartnerContent IS NULL)
                         AND (LOWER(COALESCE(Vendor,'')) NOT LIKE '%sap%')
                    THEN 1 ELSE 0 END) AS custom_count
            FROM package WHERE tenant_id = ?
        """, (self.tenant_id,)).fetchone()
        ctx['total_packages']  = pkg_counts['total']  or 0
        ctx['custom_packages'] = pkg_counts['custom_count'] or 0

        # ---- Rule 1b: Discover version comparison ----
        ctx['discover_available'] = False
        ctx['outdated_standard']  = 0
        ctx['total_standard']     = 0
        try:
            dv = conn.execute("""
                SELECT
                    COUNT(*) AS total_std,
                    SUM(CASE WHEN CurrentVersion != DiscoverVersion
                             AND DiscoverVersion != 'Manual check needed'
                             THEN 1 ELSE 0 END) AS outdated
                FROM package_discover_version
                WHERE tenant_id = ?
            """, (self.tenant_id,)).fetchone()
            if dv and dv['total_std']:
                ctx['discover_available'] = True
                ctx['total_standard']     = dv['total_std'] or 0
                ctx['outdated_standard']  = dv['outdated']  or 0
        except Exception:
            logger.debug("  Discover version table not available — Rule 1b will use neutral mid-point")

        # ---- Rule 5: tenant-wide adapter stats ----
        ctx['unique_systems'] = 0
        ctx['adapter_rows']   = []
        try:
            sys_count = conn.execute("""
                SELECT COUNT(DISTINCT LOWER(TRIM(COALESCE(address, system)))) AS cnt
                FROM bpmn_channel
                WHERE tenant_id = ?
                AND TRIM(COALESCE(address, system, '')) != ''
                AND componentType != 'ProcessDirect'
            """, (self.tenant_id,)).fetchone()
            ctx['unique_systems'] = (sys_count['cnt'] or 0) if sys_count else 0

            adapter_rows = conn.execute("""
                SELECT componentType, COUNT(*) AS cnt
                FROM bpmn_channel
                WHERE tenant_id = ?
                AND componentType IS NOT NULL
                GROUP BY componentType
            """, (self.tenant_id,)).fetchall()
            ctx['adapter_rows'] = [dict(r) for r in adapter_rows]
        except Exception:
            logger.debug("  bpmn_channel table not available — Rule 5 will score 0")

        # ---- Rule 6: certificate-to-user mappings ----
        ctx['cert_mapping_count'] = 0
        try:
            cm = conn.execute("""
                SELECT COUNT(*) AS cnt
                FROM security_certificate_user_mapping
                WHERE tenant_id = ?
            """, (self.tenant_id,)).fetchone()
            ctx['cert_mapping_count'] = (cm['cnt'] or 0) if cm else 0
        except Exception:
            logger.debug("  security_certificate_user_mapping table not available — Rule 6 will score 0")

        # ---- Total IFlows (for Rule 5 proportional allocation) ----
        total_iflows = conn.execute("""
            SELECT COUNT(*) AS cnt FROM iflow WHERE tenant_id = ?
        """, (self.tenant_id,)).fetchone()
        ctx['total_iflows'] = (total_iflows['cnt'] or 0) if total_iflows else 0

        logger.debug(
            f"  Tenant context: {ctx['total_packages']} pkgs, "
            f"{ctx['unique_systems']} systems, "
            f"{ctx['cert_mapping_count']} cert mappings, "
            f"discover_available={ctx['discover_available']}"
        )
        return ctx

    # ------------------------------------------------------------------
    # Per-package scoring
    # ------------------------------------------------------------------

    def _score_package(
        self,
        conn: sqlite3.Connection,
        pkg: sqlite3.Row,
        ctx: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute the full MCI for a single package."""

        package_id   = pkg['package_id']
        package_name = pkg['package_name']
        package_type = pkg['package_type']
        is_custom    = (package_type == 'Custom')

        # ---- Rule 1a — Custom package ratio (tenant-wide, same for all pkgs) ----
        r1a = self._rule1a(ctx)

        # ---- Rule 1b — Standard version currency ----
        r1b = self._rule1b(conn, package_id, ctx)

        # ---- Rule 2 — Artifact sync consistency ----
        r2 = self._rule2(conn, package_id)

        # ---- Rule 3 — Object complexity ----
        r3, has_timers = self._rule3(conn, package_id)

        # ---- Rule 4 — Environment variable usage ----
        r4 = self._rule4(conn, package_id) if is_custom else 0.0

        # ---- Rule 5 — Systems & adapter diversity (proportional to package IFlow share) ----
        r5 = self._rule5_for_package(conn, package_id, ctx)

        # ---- Rule 6 — Cert-to-user mappings (tenant-wide flag, same for all pkgs) ----
        r6 = self._rule6(ctx)

        # ---- Assemble total ----
        if is_custom:
            total = r1a + r1b + r2 + r3 + r4 + r5 + r6
        else:
            # Standard packages: version currency + sync are primary drivers
            # Other rules are less relevant (SAP owns the content)
            # Normalize: rule1b (max 10) × 2.5 + rule2 (max 15) × 2.0 → max ~62.5
            # Then scale to 100
            raw = (r1b * 2.5) + (r2 * 2.0)
            total = min(100.0, raw)

        total = min(100.0, max(0.0, total))
        tag   = _complexity_tag(total)

        return {
            'tenant_id':     self.tenant_id,
            'package_id':    package_id,
            'package_name':  package_name,
            'package_type':  package_type,
            'rule1a_score':  round(r1a, 2),
            'rule1b_score':  round(r1b, 2),
            'rule2_score':   round(r2,  2),
            'rule3_score':   round(r3,  2),
            'rule4_score':   round(r4,  2),
            'rule5_score':   round(r5,  2),
            'rule6_score':   round(r6,  2),
            'total_score':   round(total, 2),
            'complexity_tag': tag,
            'has_timers':    1 if has_timers else 0,
            'computed_at':   datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Individual rule calculations
    # ------------------------------------------------------------------

    def _rule1a(self, ctx: Dict[str, Any]) -> float:
        """Rule 1a: Custom package ratio → max 10 pts."""
        total = ctx['total_packages']
        if total == 0:
            return 0.0
        return (ctx['custom_packages'] / total) * 10.0

    def _rule1b(self, conn: sqlite3.Connection, package_id: str, ctx: Dict[str, Any]) -> float:
        """
        Rule 1b: Standard version currency → max 10 pts.
        Per-package: is THIS package outdated vs Discover?
        Tenant mid-point (5.0) when Discover data is unavailable.
        """
        if not ctx['discover_available']:
            return 5.0  # neutral — no data, no penalty, no credit

        try:
            row = conn.execute("""
                SELECT CurrentVersion, DiscoverVersion
                FROM package_discover_version
                WHERE tenant_id = ? AND PackageID = ?
                LIMIT 1
            """, (self.tenant_id, package_id)).fetchone()

            if row is None:
                return 0.0  # custom package or not in Discover → no version penalty
            if row['DiscoverVersion'] == 'Manual check needed':
                return 5.0  # can't tell → neutral
            if row['CurrentVersion'] != row['DiscoverVersion']:
                return 10.0  # outdated → full complexity points
            return 0.0  # up-to-date → no complexity
        except Exception:
            return 5.0

    def _rule2(self, conn: sqlite3.Connection, package_id: str) -> float:
        """Rule 2: Artifact sync consistency → max 15 pts."""
        try:
            # All 4 artifact types
            rows = conn.execute("""
                SELECT deployment_status, COUNT(*) AS cnt
                FROM (
                    SELECT CASE
                        WHEN r.Id IS NULL THEN 'Not Deployed'
                        WHEN i.Version = r.Version THEN 'In Sync'
                        ELSE 'Out of Sync'
                    END AS deployment_status
                    FROM iflow i
                    JOIN package p ON i.PackageId = p.Id AND i.tenant_id = p.tenant_id
                    LEFT JOIN runtime r ON i.Id = r.Id AND i.tenant_id = r.tenant_id
                    WHERE i.tenant_id = ? AND p.Id = ?

                    UNION ALL

                    SELECT CASE
                        WHEN r.Id IS NULL THEN 'Not Deployed'
                        WHEN sc.Version = r.Version THEN 'In Sync'
                        ELSE 'Out of Sync'
                    END AS deployment_status
                    FROM script_collection sc
                    JOIN package p ON sc.PackageId = p.Id AND sc.tenant_id = p.tenant_id
                    LEFT JOIN runtime r ON sc.Id = r.Id AND r.Type = 'SCRIPT_COLLECTION' AND sc.tenant_id = r.tenant_id
                    WHERE sc.tenant_id = ? AND p.Id = ?

                    UNION ALL

                    SELECT CASE
                        WHEN r.Id IS NULL THEN 'Not Deployed'
                        WHEN mm.Version = r.Version THEN 'In Sync'
                        ELSE 'Out of Sync'
                    END AS deployment_status
                    FROM message_mapping mm
                    JOIN package p ON mm.PackageId = p.Id AND mm.tenant_id = p.tenant_id
                    LEFT JOIN runtime r ON mm.Id = r.Id AND r.Type = 'MESSAGE_MAPPING' AND mm.tenant_id = r.tenant_id
                    WHERE mm.tenant_id = ? AND p.Id = ?

                    UNION ALL

                    SELECT CASE
                        WHEN r.Id IS NULL THEN 'Not Deployed'
                        WHEN vm.Version = r.Version THEN 'In Sync'
                        ELSE 'Out of Sync'
                    END AS deployment_status
                    FROM value_mapping vm
                    JOIN package p ON vm.PackageId = p.Id AND vm.tenant_id = p.tenant_id
                    LEFT JOIN runtime r ON vm.Id = r.Id AND r.Type = 'VALUE_MAPPING' AND vm.tenant_id = r.tenant_id
                    WHERE vm.tenant_id = ? AND p.Id = ?
                )
                GROUP BY deployment_status
            """, (
                self.tenant_id, package_id,
                self.tenant_id, package_id,
                self.tenant_id, package_id,
                self.tenant_id, package_id,
            )).fetchall()

            counts = {r['deployment_status']: r['cnt'] for r in rows}
            total = sum(counts.values())
            if total == 0:
                return 0.0

            not_deployed = counts.get('Not Deployed', 0)
            out_of_sync  = counts.get('Out of Sync', 0)
            weighted     = (not_deployed * 1.0) + (out_of_sync * 0.8)
            return min(15.0, (weighted / total) * 15.0)

        except Exception as e:
            logger.debug(f"  Rule 2 error for {package_id}: {e}")
            return 0.0

    def _rule3(self, conn: sqlite3.Connection, package_id: str) -> Tuple[float, bool]:
        """
        Rule 3: Object complexity → max 10 pts.
        Returns (score, has_timers).
        """
        score = 0.0
        has_timers = False

        try:
            # Weighted step score per IFlow
            act_rows = conn.execute("""
                SELECT iflowId,
                       activityType,
                       subActivityType,
                       COUNT(*) AS step_count
                FROM bpmn_activity
                WHERE tenant_id = ? AND packageId = ?
                GROUP BY iflowId, activityType, subActivityType
            """, (self.tenant_id, package_id)).fetchall()

            if act_rows:
                # Aggregate weighted scores per IFlow
                iflow_scores: Dict[str, float] = {}
                for row in act_rows:
                    iflow_id     = row['iflowId']
                    sub_type     = row['subActivityType'] or row['activityType'] or ''
                    weight       = ACTIVITY_WEIGHTS.get(sub_type, ACTIVITY_DEFAULT_WEIGHT)
                    wt_score     = weight * row['step_count']
                    iflow_scores[iflow_id] = iflow_scores.get(iflow_id, 0.0) + wt_score

                avg_weighted = sum(iflow_scores.values()) / len(iflow_scores)
                score = min(10.0, avg_weighted / RULE3_STEP_BASELINE)
        except Exception as e:
            logger.debug(f"  Rule 3 (activities) error for {package_id}: {e}")

        # Check for timer IFlows in this package
        try:
            timer_count = conn.execute("""
                SELECT COUNT(*) AS cnt
                FROM bpmn_timer
                WHERE tenant_id = ? AND packageId = ?
            """, (self.tenant_id, package_id)).fetchone()
            has_timers = (timer_count['cnt'] > 0) if timer_count else False
        except Exception:
            pass

        return round(score, 2), has_timers

    def _rule4(self, conn: sqlite3.Connection, package_id: str) -> float:
        """Rule 4: Environment variable (HC_) usage → max 25 pts."""
        try:
            rows = conn.execute("""
                SELECT fileType, COUNT(*) AS file_count
                FROM environment_variable_check evc
                JOIN package p ON evc.packageId = p.Id AND evc.tenant_id = p.tenant_id
                WHERE evc.tenant_id = ? AND p.Id = ?
                GROUP BY fileType
            """, (self.tenant_id, package_id)).fetchall()

            if not rows:
                return 0.0

            weighted = sum(
                row['file_count'] * ENV_VAR_FILE_WEIGHTS.get(row['fileType'] or '', ENV_VAR_DEFAULT_WEIGHT)
                for row in rows
            )
            return min(25.0, (weighted / RULE4_BASELINE) * 25.0)

        except Exception as e:
            logger.debug(f"  Rule 4 error for {package_id}: {e}")
            return 0.0

    def _rule5_for_package(
        self,
        conn: sqlite3.Connection,
        package_id: str,
        ctx: Dict[str, Any]
    ) -> float:
        """
        Rule 5: Systems & adapter diversity → max 20 pts.
        Uses a package's proportional share of the tenant-wide score
        (based on what fraction of total IFlows this package contributes).
        """
        # Tenant-level Rule 5 score
        tenant_r5 = self._rule5_tenant(ctx)
        if tenant_r5 == 0.0:
            return 0.0

        # Proportional share by IFlow count
        try:
            pkg_iflows = conn.execute("""
                SELECT COUNT(*) AS cnt FROM iflow
                WHERE tenant_id = ? AND PackageId = ?
            """, (self.tenant_id, package_id)).fetchone()
            pkg_iflow_count = (pkg_iflows['cnt'] or 0) if pkg_iflows else 0
        except Exception:
            pkg_iflow_count = 0

        total_iflows = ctx.get('total_iflows', 0)
        if total_iflows == 0:
            return 0.0

        proportion = pkg_iflow_count / total_iflows
        return round(tenant_r5 * proportion, 2)

    def _rule5_tenant(self, ctx: Dict[str, Any]) -> float:
        """Compute tenant-level Rule 5 score (5a + 5b), max 20 pts."""
        # 5a: system count (max 10 pts, piecewise linear)
        n = ctx['unique_systems']
        if n <= 10:
            s5a = (n / 10.0) * 4.0
        elif n <= 30:
            s5a = 4.0 + ((n - 10) / 20.0) * 4.0
        elif n <= 60:
            s5a = 8.0 + ((n - 30) / 30.0) * 2.0
        else:
            s5a = 10.0
        s5a = min(10.0, s5a)

        # 5b: adapter complexity tier (max 10 pts)
        adapter_weighted = sum(
            row['cnt'] * ADAPTER_TIER_WEIGHTS.get(row['componentType'], ADAPTER_DEFAULT_WEIGHT)
            for row in ctx['adapter_rows']
        )
        s5b = min(10.0, (adapter_weighted / RULE5B_BASELINE) * 10.0)

        return s5a + s5b

    def _rule6(self, ctx: Dict[str, Any]) -> float:
        """Rule 6: Certificate-to-user mappings → max 10 pts."""
        return min(10.0, ctx['cert_mapping_count'] * RULE6_MULTIPLIER)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _insert_scores(self, conn: sqlite3.Connection, rows: List[Dict[str, Any]]):
        """Bulk insert scored rows into package_migration_score."""
        conn.executemany("""
            INSERT INTO package_migration_score
            (tenant_id, package_id, package_name, package_type,
             rule1a_score, rule1b_score, rule2_score, rule3_score,
             rule4_score, rule5_score, rule6_score,
             total_score, complexity_tag, has_timers, computed_at)
            VALUES
            (:tenant_id, :package_id, :package_name, :package_type,
             :rule1a_score, :rule1b_score, :rule2_score, :rule3_score,
             :rule4_score, :rule5_score, :rule6_score,
             :total_score, :complexity_tag, :has_timers, :computed_at)
        """, rows)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a summary dict for logging and the report header."""
        if not rows:
            return {
                'overall_mci': 0.0,
                'overall_tag': 'Low',
                'custom_mci': 0.0,
                'standard_mci': 0.0,
                'total_packages': 0,
                'tag_counts': {},
            }

        total_pkgs  = len(rows)
        custom_rows  = [r for r in rows if r['package_type'] == 'Custom']
        standard_rows = [r for r in rows if r['package_type'] != 'Custom']

        custom_mci   = (sum(r['total_score'] for r in custom_rows)   / len(custom_rows))   if custom_rows   else 0.0
        standard_mci = (sum(r['total_score'] for r in standard_rows) / len(standard_rows)) if standard_rows else 0.0

        # Weighted overall
        overall_mci = (
            (custom_mci   * len(custom_rows)   / total_pkgs) +
            (standard_mci * len(standard_rows) / total_pkgs)
        )

        tag_counts: Dict[str, int] = {}
        for r in rows:
            tag = r['complexity_tag']
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            'overall_mci':    round(overall_mci, 1),
            'overall_tag':    _complexity_tag(overall_mci),
            'custom_mci':     round(custom_mci, 1),
            'standard_mci':   round(standard_mci, 1),
            'total_packages': total_pkgs,
            'tag_counts':     tag_counts,
        }