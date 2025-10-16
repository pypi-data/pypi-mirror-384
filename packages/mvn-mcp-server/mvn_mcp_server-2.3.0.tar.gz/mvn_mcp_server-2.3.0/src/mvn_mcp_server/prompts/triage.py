"""
Dependency Triage prompt for comprehensive Maven dependency analysis.

Provides structured workflow for analyzing dependencies and creating
enterprise-grade vulnerability triage reports with full traceability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

# Define Message type for development/testing
Message = Dict[str, Any]


async def dependency_triage(
    service_name: str, workspace: Optional[str] = None
) -> List[Message]:
    """Analyze service dependencies and create comprehensive vulnerability triage report."""

    workspace_path = workspace or f"./{service_name}"
    timestamp = datetime.now().isoformat()

    content = f"""# Maven Dependency Triage Analysis 🔍

**Service:** {service_name}
**Workspace:** {workspace_path}
**Analysis Date:** {timestamp}

You are performing a comprehensive dependency triage analysis following enterprise workflow best practices. This analysis will become the foundation for the subsequent update planning phase.

## Triage Analysis Workflow

### Phase 1: Project Discovery
**Objective:** Map the Maven project structure and dependency landscape

**Tasks:**
1. **POM Hierarchy Analysis**
   - Search for all POM files: `{workspace_path}/**/pom.xml`
   - Map parent-child relationships and inheritance
   - Identify multi-module structure
   - Document dependency management strategy
   - Focus on main modules (exclude test/sample projects)

2. **Dependency Extraction**
   - Extract all `<dependency>` declarations from each POM
   - Identify managed dependencies from parent POMs
   - Note version variables and properties
   - Map dependencies to their declaring modules

### Phase 2: Version Analysis
**Objective:** Assess current state vs available updates

**Tasks:**
3. **Batch Version Checking**
   - Use `check_version_batch_tool` with ALL discovered dependencies
   - Categorize updates: MAJOR/MINOR/PATCH
   - Calculate age of current versions
   - Identify stale dependencies (>1 year old)

4. **Version Compatibility Assessment**
   - Use `list_available_versions_tool` for critical dependencies
   - Check release notes for breaking changes
   - Identify version compatibility constraints

### Phase 3: Security Assessment
**Objective:** Identify and prioritize security vulnerabilities

**Tasks:**
5. **Vulnerability Scanning**
   - Execute `scan_java_project_tool`:
     - workspace: `{workspace_path}`
     - scan_mode: "workspace" (or "pom_only" for token efficiency)
     - severity_filter: ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
     - max_results: 100
   - Cross-reference scan results with version analysis

6. **Risk Prioritization**
   - Correlate CVE data with dependency versions
   - Assess exploitability and impact
   - Map vulnerabilities to fix versions

### Phase 4: Triage Report Generation
**Objective:** Create comprehensive triage report for planning phase

**Required Report Structure:**

# {service_name} Service — Dependency Triage Report 🔍

**Report ID:** {service_name}-triage-{timestamp[:10]}
**Analysis Date:** {timestamp}
**Workspace:** {workspace_path}

## Executive Summary
- **Total Dependencies:** [count]
- **Vulnerabilities Found:** [count] (Critical: X, High: Y, Medium: Z)
- **Outdated Dependencies:** [count]/[total] ([percentage]%)
- **Recommended Actions:** [count] (Immediate: X, This Sprint: Y, Next Sprint: Z)

## Critical Findings (Action Required)

### Security Vulnerabilities
| CVE ID | Severity | Dependency | Current | Fix Version | CVSS | Description |
|--------|----------|------------|---------|-------------|------|-------------|
| CVE-XXXX-YYYY | CRITICAL | log4j-core | 2.14.1 | 2.17.1+ | 9.0 | Remote code execution |

### Severely Outdated Dependencies
| Dependency | Current | Latest | Age | Update Type | Risk Level |
|------------|---------|--------|-----|-------------|------------|
| spring-core | 4.3.30 | 6.1.2 | 3.2 years | MAJOR | HIGH |

## Standard Findings (Planned Updates)

### Version Updates Available
| Dependency | Current | Latest Stable | Update Type | Module Location |
|------------|---------|---------------|-------------|-----------------|
| jackson-databind | 2.13.0 | 2.16.1 | MINOR | parent-pom.xml |

### Dependencies Analysis Summary
- **Up to Date:** [count] dependencies
- **Minor Updates:** [count] dependencies
- **Major Updates:** [count] dependencies
- **Security Updates:** [count] dependencies

## Project Structure Analysis

### POM Hierarchy
```
parent-pom.xml (defines versions)
├── core-module/pom.xml
├── api-module/pom.xml
└── service-module/pom.xml
```

### Dependency Management Strategy
- Version management: [Centralized/Distributed]
- Property usage: [Property names for major deps]
- BOM usage: [Spring Boot BOM, etc.]

## Recommended Update Strategy

### Phase 1: Critical Security (Immediate)
**Priority:** CRITICAL - Deploy within 24-48 hours
**Risk:** LOW - Well-tested security patches

1. **CVE-XXXX-YYYY: log4j-core 2.14.1 → 2.17.1**
   - **Fix Location:** parent-pom.xml line 42
   - **Change:** `<log4j.version>2.17.1</log4j.version>`
   - **Impact:** Security vulnerability resolution
   - **Testing:** Smoke tests + security scan verification

### Phase 2: High Priority Updates (This Sprint)
**Priority:** HIGH - Complete within current sprint
**Risk:** MEDIUM - May require integration testing

[List specific updates with details]

### Phase 3: Maintenance Updates (Next Sprint)
**Priority:** MEDIUM - Complete in next maintenance window
**Risk:** LOW - Standard version bumps

[List remaining updates]

## Implementation Artifacts

### Files Requiring Updates
- `parent-pom.xml` (line references for each change)
- `core-module/pom.xml` (specific dependency overrides)
- [Additional POM files as needed]

### Version Control Strategy
**Recommended Branch:** `feature/security-updates-{service_name}`
**Commit Pattern:** `fix(deps): update [dependency] to [version] for [CVE/reason]`
**PR Template:** Include security scan results and test evidence

## Testing Requirements
- [ ] All unit tests pass
- [ ] Integration tests complete successfully
- [ ] Security scan shows resolved vulnerabilities
- [ ] No new vulnerabilities introduced
- [ ] Application startup verification
- [ ] Smoke tests for critical paths

## Success Criteria
- All CRITICAL and HIGH vulnerabilities resolved
- No build failures or test regressions
- Security scan passes with acceptable risk level
- Dependencies updated to secure, stable versions
- Documentation updated with changes

---
**Next Step:** Use `plan` prompt with this triage report to create implementation plan

### Phase 5: Resource Storage
**Objective:** Store triage results for subsequent planning

**Tasks:**
7. **Store Triage Report**
   - Save complete report to: `triage://reports/{service_name}/latest`
   - Include metadata: timestamp, workspace, dependency counts
   - Store raw scan data for plan generation

8. **Prepare for Planning Phase**
   - Validate all required data is captured
   - Confirm report structure matches planning requirements
   - Signal completion for next workflow step

## Critical Success Factors
- **Completeness:** Include ALL dependencies and vulnerabilities
- **Accuracy:** Verify version information and CVE details
- **Actionability:** Provide specific file locations and change instructions
- **Traceability:** Link each finding to specific dependencies and modules

## Implementation Guidelines

### Tool Usage Sequence
1. **Project Discovery:** Use file system exploration to find POMs
2. **Dependency Analysis:** Use `check_version_batch_tool` for all dependencies
3. **Security Scanning:** Use `scan_java_project_tool` for comprehensive analysis
4. **Version Research:** Use `list_available_versions_tool` for critical updates

### Data Collection Requirements
- Extract complete dependency list with versions and locations
- Capture vulnerability data with CVE IDs and severity levels
- Document POM structure and inheritance relationships
- Identify version properties and BOM usage patterns

### Report Quality Standards
- All vulnerabilities must include CVE IDs and fix versions
- All dependencies must include current version and latest available
- All recommendations must include specific file locations
- All findings must be categorized by priority and risk level

**Begin comprehensive triage analysis now. The quality of this analysis directly impacts the effectiveness of the subsequent update planning phase.**"""

    return [{"role": "user", "content": content}]
