"""
Update Plan prompt for creating structured remediation plans.

Provides structured workflow for creating actionable update plans based on
triage reports with full traceability and enterprise workflow patterns.
"""

from typing import List, Optional, Dict, Any

# Define Message type for development/testing
Message = Dict[str, Any]


async def update_plan(
    service_name: str, priorities: Optional[List[str]] = None
) -> List[Message]:
    """Create detailed remediation plan based on vulnerability triage report following enterprise workflow patterns."""

    priority_filter = priorities or ["CRITICAL", "HIGH"]

    content = f"""# Maven Remediation Plan Creation 📋

You are creating a detailed remediation plan for **{service_name}** based on the vulnerability triage report, following enterprise workflow best practices.

## Your Task

### 1. Retrieve and Analyze Triage Report
Access the triage report from: `triage://reports/{service_name}/latest`

Before drafting the final plan, work inside <triage_breakdown> tags to:
- Extract and list all vulnerabilities mentioned in the triage report
- Categorize vulnerabilities by severity (CRITICAL, HIGH, MEDIUM, LOW)
- List all outdated dependencies and their current/target versions
- Note specific POM files that need updating
- Brainstorm Maven-specific considerations

### 2. Create Structured Remediation Plan

Generate a plan following this proven enterprise structure:

# {service_name} Service — Remediation Plan

## Overview
Brief description tying this plan to the triage report findings and total issues identified.

## References
- Triage Report: {service_name}_triage_YYYY-MM-DD.md
- Maven Central documentation
- Relevant CVEs: [list specific CVEs from triage]

## Phases and Tasks

### Phase 1: Update Critical Dependencies
- [ ] **Update [dependency] from [current] to [target]**
  _Ref: [CVE-ID] ([description]), Triage Table_
  - Edit [specific-pom.xml file]
  - Property: `<[dependency].version>[target]</[dependency].version>`
  - Verify with: `check_version_tool("[groupId]:[artifactId]", "[target]")`

### Phase 2: Update High Priority Dependencies
- [ ] **Update [dependency] from [current] to [target]**
  _Ref: [CVE-ID] ([description]), Triage Table_
  - [Specific implementation steps]

### Phase 3: Update Medium/Low Priority Dependencies
- [ ] [List remaining updates with same detailed format]

### Phase 4: Security Hardening & Verification
- [ ] Review transitive dependencies for affected libraries
- [ ] Run full security scan: `scan_java_project_tool("{service_name}", scan_mode="workspace")`
- [ ] Validate no new vulnerabilities introduced

### Phase 5: Build & Test Verification
- [ ] Build all updated modules: `mvn clean install`
- [ ] Run unit tests: `mvn test`
- [ ] Run integration tests: `mvn verify`
- [ ] Validate service functionality in staging environment

## Success Criteria
- All CRITICAL and HIGH vulnerabilities are remediated
- All listed dependencies updated to recommended versions
- No new critical/high vulnerabilities introduced
- All builds and tests pass successfully
- Service functionality verified in staging

## Dependency Updates Summary

| Dependency | Current | Target | Module | Priority |
|------------|---------|--------|--------|----------|
| [name] | [version] | [version] | [pom-location] | [CRITICAL/HIGH/MEDIUM] |

## Version Control Conventions
- **Branch naming:** `remediate/{service_name}-vuln-YYYY-MM`
- **Commit message format:**
  `fix({service_name}): update [dependency] to [version] for [CVE-ID]`
- **Required PR checks:**
  - Build passes (`mvn clean install`)
  - All tests pass (`mvn verify`)
  - Security scan passes (zero CRITICAL/HIGH)
  - Peer review completed

## Progress Checklist
- [ ] Phase 1: Critical updates complete
- [ ] Phase 2: High priority updates complete
- [ ] Phase 3: Medium/low updates complete
- [ ] Phase 4: Security hardening complete
- [ ] Phase 5: Build & test verification complete
- [ ] Success criteria met

### 3. Implementation Guidelines
- **Traceability:** Every task must link back to specific triage findings (CVE IDs, dependency analysis)
- **Specificity:** Include exact POM file locations and Maven property names
- **Tool Integration:** Reference specific MCP tools for validation (`check_version_tool`, `scan_java_project_tool`)
- **Checkboxes:** Ensure all tasks start unchecked ([ ]) regardless of current progress
- **Priority Focus:** Emphasize {', '.join(priority_filter)} priority items

### 4. Critical Requirements
- Link each task back to specific triage item or CVE for traceability
- Use clear, concise language throughout the plan
- Include specific version updates for dependencies
- Add build verification phase
- Specify branch naming convention and commit message format
- List required PR checks

### 5. Plan Structure Requirements

#### Task Format Standards
Each update task must include:
- **Dependency name:** Clear Maven coordinates
- **Version change:** Current → Target with rationale
- **Traceability:** Direct reference to CVE or triage finding
- **Implementation:** Specific file and line changes
- **Verification:** Tool commands to validate success

#### Phase Organization Standards
- **Phase 1 (CRITICAL):** Security vulnerabilities, deploy within 24-48 hours
- **Phase 2 (HIGH):** Important updates, complete within current sprint
- **Phase 3 (MEDIUM/LOW):** Maintenance updates, next sprint
- **Phase 4:** Security verification and hardening
- **Phase 5:** Build and test validation

#### Success Criteria Standards
- All security vulnerabilities resolved
- No regression in functionality or tests
- Security scan validation passes
- Build process remains stable
- Documentation updated appropriately

### 6. Maven-Specific Considerations

#### Dependency Management Patterns
- **Parent POM Updates:** Focus on centralized version management
- **BOM Management:** Handle Spring Boot and other BOMs appropriately
- **Property Updates:** Use version properties for consistent updates
- **Transitive Dependencies:** Consider impact on indirect dependencies

#### Testing and Validation
- **Version Conflicts:** Check for dependency conflicts after updates
- **API Compatibility:** Validate no breaking changes in major updates
- **Performance Impact:** Consider performance implications of updates
- **Security Scanning:** Verify vulnerabilities are actually resolved

### 7. Quality Assurance Checklist

Before finalizing the plan, ensure:
- [ ] Every task references specific triage findings
- [ ] All CVE IDs from triage are addressed
- [ ] File locations are specific and accurate
- [ ] Tool commands are correct and actionable
- [ ] Priority ordering follows enterprise standards
- [ ] Success criteria are measurable and specific

### 8. Final Steps
After creating the remediation plan:
- Store the plan at: `plans://updates/{service_name}/latest`
- Present only the final remediation plan in markdown format
- Ask if the plan should be saved with naming: `{service_name}_plan_YYYY-MM-DD.md`

**Priority Focus:** {', '.join(priority_filter)}

**Important:** The plan must demonstrate clear traceability from each task back to specific triage findings. Every dependency update should reference the CVE ID, vulnerability description, or staleness analysis that drives the need for the update.

Begin creating the remediation plan now, ensuring it follows the proven enterprise structure with full traceability to triage findings."""

    return [{"role": "user", "content": content}]
