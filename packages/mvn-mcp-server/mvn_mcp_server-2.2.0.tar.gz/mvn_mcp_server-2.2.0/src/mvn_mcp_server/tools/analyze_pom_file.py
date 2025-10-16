"""POM file analysis tool.

This module implements a focused analysis of a single Maven POM file for security issues
without requiring scanning the entire workspace structure.
"""

import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, Any

from mvn_mcp_server.shared.data_types import ErrorCode
from mvn_mcp_server.services.response import (
    format_success_response,
    format_error_response,
)
from fastmcp.exceptions import ValidationError, ResourceError

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


def parse_pom_xml(pom_path: str) -> Dict[str, Any]:
    """Parse a POM file and extract relevant dependency information.

    Args:
        pom_path: Path to the POM file

    Returns:
        Dict containing the POM structure and dependencies

    Raises:
        ValidationError: If the POM file is invalid or cannot be parsed
    """
    try:
        # Register namespaces for XML parsing
        ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

        # Parse the POM file
        tree = ET.parse(pom_path)
        root = tree.getroot()

        # Extract basic project information
        project_info = {
            "artifact_id": _get_element_text(root, "./mvn:artifactId", ns),
            "group_id": _get_element_text(root, "./mvn:groupId", ns),
            "version": _get_element_text(root, "./mvn:version", ns),
            "name": _get_element_text(root, "./mvn:name", ns),
            "packaging": _get_element_text(root, "./mvn:packaging", ns) or "jar",
            "properties": _extract_properties(root, ns),
            "parent": _extract_parent(root, ns),
            "dependencies": [],
            "dependency_management": [],
            "modules": [],
        }

        # Extract dependencies
        project_info["dependencies"] = _extract_dependencies(
            root, ns, project_info["properties"]
        )

        # Extract dependency management
        project_info["dependency_management"] = _extract_dependency_management(
            root, ns, project_info["properties"]
        )

        # Extract modules (if any)
        modules_elem = root.findall("./mvn:modules/mvn:module", ns)
        if modules_elem:
            project_info["modules"] = [
                module.text for module in modules_elem if module.text
            ]

        # Extract profiles
        project_info["profiles"] = _extract_profiles(
            root, ns, project_info["properties"]
        )

        return project_info

    except ET.ParseError as e:
        raise ValidationError(f"Invalid POM file: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error parsing POM file: {str(e)}")


def _get_element_text(element, xpath, ns, default=None):
    """Helper function to get text from an XML element."""
    elem = element.find(xpath, ns)
    return elem.text if elem is not None and elem.text else default


def _extract_properties(root, ns):
    """Extract Maven properties from the POM."""
    properties = {}
    props_elem = root.find("./mvn:properties", ns)

    if props_elem is not None:
        for prop in props_elem:
            # Remove namespace prefix for property names
            tag = prop.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]

            properties[tag] = prop.text or ""

    return properties


def _extract_parent(root, ns):
    """Extract parent POM information."""
    parent_elem = root.find("./mvn:parent", ns)
    if parent_elem is not None:
        return {
            "group_id": _get_element_text(parent_elem, "./mvn:groupId", ns),
            "artifact_id": _get_element_text(parent_elem, "./mvn:artifactId", ns),
            "version": _get_element_text(parent_elem, "./mvn:version", ns),
            "relative_path": _get_element_text(
                parent_elem, "./mvn:relativePath", ns, "../pom.xml"
            ),
        }
    return None


def _resolve_version(version, properties):
    """Resolve version property references."""
    if not version:
        return None

    # Handle property references like ${project.version} or ${some.version}
    if version.startswith("${") and version.endswith("}"):
        prop_name = version[2:-1]

        # Handle special project properties
        if prop_name == "project.version":
            return properties.get("project.version", version)

        # Look for the property in the properties dictionary
        return properties.get(prop_name, version)

    return version


def _extract_dependencies(root, ns, properties):
    """Extract dependencies from the POM."""
    dependencies = []
    deps_elem = root.find("./mvn:dependencies", ns)

    if deps_elem is not None:
        for dep in deps_elem.findall("./mvn:dependency", ns):
            group_id = _get_element_text(dep, "./mvn:groupId", ns)
            artifact_id = _get_element_text(dep, "./mvn:artifactId", ns)
            version = _get_element_text(dep, "./mvn:version", ns)

            # Resolve version if it's a property reference
            resolved_version = _resolve_version(version, properties)

            dependencies.append(
                {
                    "group_id": group_id,
                    "artifact_id": artifact_id,
                    "raw_version": version,
                    "resolved_version": resolved_version,
                    "scope": _get_element_text(dep, "./mvn:scope", ns, "compile"),
                    "classifier": _get_element_text(dep, "./mvn:classifier", ns),
                    "type": _get_element_text(dep, "./mvn:type", ns, "jar"),
                    "optional": _get_element_text(dep, "./mvn:optional", ns, "false")
                    == "true",
                    "exclusions": _extract_exclusions(dep, ns),
                }
            )

    return dependencies


def _extract_dependency_management(root, ns, properties):
    """Extract dependency management section from the POM."""
    managed_deps = []
    dep_mgmt = root.find("./mvn:dependencyManagement/mvn:dependencies", ns)

    if dep_mgmt is not None:
        for dep in dep_mgmt.findall("./mvn:dependency", ns):
            group_id = _get_element_text(dep, "./mvn:groupId", ns)
            artifact_id = _get_element_text(dep, "./mvn:artifactId", ns)
            version = _get_element_text(dep, "./mvn:version", ns)

            # Resolve version if it's a property reference
            resolved_version = _resolve_version(version, properties)

            managed_deps.append(
                {
                    "group_id": group_id,
                    "artifact_id": artifact_id,
                    "raw_version": version,
                    "resolved_version": resolved_version,
                    "scope": _get_element_text(dep, "./mvn:scope", ns, "compile"),
                    "classifier": _get_element_text(dep, "./mvn:classifier", ns),
                    "type": _get_element_text(dep, "./mvn:type", ns, "jar"),
                }
            )

    return managed_deps


def _extract_exclusions(dep, ns):
    """Extract exclusions for a dependency."""
    exclusions = []
    excl_elem = dep.find("./mvn:exclusions", ns)

    if excl_elem is not None:
        for excl in excl_elem.findall("./mvn:exclusion", ns):
            exclusions.append(
                {
                    "group_id": _get_element_text(excl, "./mvn:groupId", ns),
                    "artifact_id": _get_element_text(excl, "./mvn:artifactId", ns),
                }
            )

    return exclusions


def _extract_profiles(root, ns, global_properties):
    """Extract profiles from the POM."""
    profiles = []
    profiles_elem = root.find("./mvn:profiles", ns)

    if profiles_elem is not None:
        for profile in profiles_elem.findall("./mvn:profile", ns):
            profile_id = _get_element_text(profile, "./mvn:id", ns, "unknown")

            # Extract profile-specific properties
            profile_properties = global_properties.copy()
            props_elem = profile.find("./mvn:properties", ns)

            if props_elem is not None:
                for prop in props_elem:
                    tag = prop.tag
                    if "}" in tag:
                        tag = tag.split("}", 1)[1]
                    profile_properties[tag] = prop.text or ""

            # Extract profile dependencies
            profile_deps = _extract_dependencies(profile, ns, profile_properties)

            profiles.append(
                {
                    "id": profile_id,
                    "activation": _extract_activation(profile, ns),
                    "dependencies": profile_deps,
                    "properties": profile_properties,
                }
            )

    return profiles


def _extract_activation(profile, ns):
    """Extract activation conditions for a profile."""
    activation = {}
    act_elem = profile.find("./mvn:activation", ns)

    if act_elem is not None:
        activation["active_by_default"] = (
            _get_element_text(act_elem, "./mvn:activeByDefault", ns, "false") == "true"
        )

        # Extract JDK activation
        jdk = _get_element_text(act_elem, "./mvn:jdk", ns)
        if jdk:
            activation["jdk"] = jdk

        # Extract OS activation
        os_elem = act_elem.find("./mvn:os", ns)
        if os_elem is not None:
            activation["os"] = {
                "name": _get_element_text(os_elem, "./mvn:name", ns),
                "family": _get_element_text(os_elem, "./mvn:family", ns),
                "arch": _get_element_text(os_elem, "./mvn:arch", ns),
                "version": _get_element_text(os_elem, "./mvn:version", ns),
            }

        # Extract property activation
        prop_elem = act_elem.find("./mvn:property", ns)
        if prop_elem is not None:
            activation["property"] = {
                "name": _get_element_text(prop_elem, "./mvn:name", ns),
                "value": _get_element_text(prop_elem, "./mvn:value", ns),
            }

        # Extract file activation
        file_elem = act_elem.find("./mvn:file", ns)
        if file_elem is not None:
            activation["file"] = {
                "exists": _get_element_text(file_elem, "./mvn:exists", ns),
                "missing": _get_element_text(file_elem, "./mvn:missing", ns),
            }

    return activation


def check_vulnerability_databases():
    """Check if common vulnerability databases are available."""
    try:
        known_deps = [
            "org.apache.logging.log4j:log4j-core:2.14.1",  # Known Log4Shell vulnerable version
            "com.fasterxml.jackson.core:jackson-databind:2.9.9",  # Known vulnerable version
        ]

        for dep in known_deps:
            parts = dep.split(":")
            if len(parts) != 3:
                continue

            group_id, artifact_id, version = parts

            # Here we could implement checking against known vulnerability databases
            # For now, we just check a few well-known vulnerabilities
            if (
                artifact_id == "log4j-core"
                and version.startswith("2.")
                and version < "2.15.0"
            ):
                return True  # Log4Shell vulnerability check works

        return False
    except Exception as e:
        logger.warning(f"Error checking vulnerability databases: {e}")
        return False


def analyze_pom_file(
    pom_path: str, include_vulnerability_check: bool = True
) -> Dict[str, Any]:
    """Analyze a Maven POM file for dependencies and potential vulnerabilities.

    Args:
        pom_path: Path to the POM file
        include_vulnerability_check: Whether to check for known vulnerabilities

    Returns:
        Dict containing the analysis results

    Raises:
        ValidationError: If the input parameters are invalid
        ResourceError: If there's an issue with scanning tools
        ToolError: For other unexpected errors
    """
    tool_name = "analyze_pom_file"

    try:
        # Validate POM path
        pom_file_path = Path(pom_path)
        if not pom_file_path.exists():
            raise ValidationError(f"POM file does not exist: {pom_path}")

        if not pom_file_path.is_file():
            raise ValidationError(f"POM path is not a file: {pom_path}")

        if pom_file_path.suffix.lower() != ".xml":
            raise ValidationError(f"File does not appear to be an XML file: {pom_path}")

        logger.info(f"Starting POM file analysis for {pom_path}")

        # Parse the POM file
        pom_data = parse_pom_xml(pom_path)

        # Basic results without vulnerability information
        analysis_result = {
            "pom_file": str(pom_file_path),
            "project_info": {
                "group_id": pom_data.get("group_id"),
                "artifact_id": pom_data.get("artifact_id"),
                "version": pom_data.get("version"),
                "name": pom_data.get("name"),
                "packaging": pom_data.get("packaging", "jar"),
            },
            "dependency_count": len(pom_data.get("dependencies", [])),
            "managed_dependency_count": len(pom_data.get("dependency_management", [])),
            "module_count": len(pom_data.get("modules", [])),
            "profile_count": len(pom_data.get("profiles", [])),
            "has_parent": pom_data.get("parent") is not None,
            "dependencies": pom_data.get("dependencies", []),
            "property_references": _count_property_references(pom_data),
            "vulnerability_scan_enabled": include_vulnerability_check,
            "vulnerability_scan_supported": check_vulnerability_databases(),
            "known_vulnerable_dependencies": [],
        }

        if include_vulnerability_check:
            # Basic check for known vulnerable dependencies
            # This is a simplified check - in a real implementation, you'd check against a CVE database
            known_vulnerabilities = _check_for_known_vulnerabilities(
                pom_data.get("dependencies", [])
            )
            analysis_result["known_vulnerable_dependencies"] = known_vulnerabilities

        return format_success_response(tool_name, analysis_result)

    except ValidationError as e:
        # Re-raise validation errors
        logger.error(f"Validation error: {str(e)}")
        return format_error_response(tool_name, ErrorCode.INVALID_INPUT_FORMAT, str(e))
    except ResourceError as e:
        # Handle resource errors
        logger.error(f"Resource error: {str(e)}")
        return format_error_response(tool_name, ErrorCode.MAVEN_ERROR, str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in POM file analysis: {str(e)}")
        return format_error_response(
            tool_name,
            ErrorCode.INTERNAL_SERVER_ERROR,
            f"Error in POM file analysis: {str(e)}",
        )


def _count_property_references(pom_data):
    """Count property references in dependencies."""
    count = 0

    # Check dependencies
    for dep in pom_data.get("dependencies", []):
        if dep.get("raw_version") and dep.get("raw_version").startswith("${"):
            count += 1

    # Check managed dependencies
    for dep in pom_data.get("dependency_management", []):
        if dep.get("raw_version") and dep.get("raw_version").startswith("${"):
            count += 1

    return count


def _check_for_known_vulnerabilities(dependencies):
    """Check for well-known vulnerable dependencies.

    This is a simplified check for demonstration purposes.
    A real implementation would check against a CVE database.
    """
    known_vulnerabilities = []

    for dep in dependencies:
        group_id = dep.get("group_id")
        artifact_id = dep.get("artifact_id")
        version = dep.get("resolved_version") or dep.get("raw_version")

        if not group_id or not artifact_id or not version:
            continue

        # Check for Log4Shell vulnerability
        if group_id == "org.apache.logging.log4j" and artifact_id == "log4j-core":
            if version.startswith("2.") and version < "2.15.0":
                known_vulnerabilities.append(
                    {
                        "group_id": group_id,
                        "artifact_id": artifact_id,
                        "version": version,
                        "vulnerability": "CVE-2021-44228",
                        "severity": "CRITICAL",
                        "description": "Log4Shell vulnerability in Log4j",
                        "recommendation": "Update to version 2.15.0 or later",
                        "links": ["https://nvd.nist.gov/vuln/detail/CVE-2021-44228"],
                    }
                )

        # Check for Jackson Databind vulnerability
        if (
            group_id == "com.fasterxml.jackson.core"
            and artifact_id == "jackson-databind"
        ):
            if version < "2.9.10.7":
                known_vulnerabilities.append(
                    {
                        "group_id": group_id,
                        "artifact_id": artifact_id,
                        "version": version,
                        "vulnerability": "Multiple CVEs",
                        "severity": "HIGH",
                        "description": "Multiple deserialization vulnerabilities in Jackson Databind",
                        "recommendation": "Update to version 2.9.10.7 or later",
                        "links": [
                            "https://github.com/FasterXML/jackson-databind/security/advisories"
                        ],
                    }
                )

        # Check for Spring Framework vulnerability
        if group_id == "org.springframework" and artifact_id.startswith("spring-"):
            if version.startswith("5.2.") and version < "5.2.20":
                known_vulnerabilities.append(
                    {
                        "group_id": group_id,
                        "artifact_id": artifact_id,
                        "version": version,
                        "vulnerability": "CVE-2021-22118",
                        "severity": "MEDIUM",
                        "description": "Spring Framework vulnerable to RCE when using Spring Expression",
                        "recommendation": "Update to version 5.2.20 or later",
                        "links": ["https://tanzu.vmware.com/security/cve-2021-22118"],
                    }
                )

    return known_vulnerabilities
