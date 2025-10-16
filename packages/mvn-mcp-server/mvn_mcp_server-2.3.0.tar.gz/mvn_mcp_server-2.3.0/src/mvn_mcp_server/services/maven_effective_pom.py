"""Maven Effective POM Service for profile-based dependency resolution.

This service provides functionality to generate effective POMs for Maven profiles,
enabling accurate dependency resolution and profile-specific security scanning.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from fastmcp.exceptions import ResourceError

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


class MavenEffectivePomService:
    """Service for generating effective POMs using Maven."""

    # Class variable to track generated POMs for cleanup
    _generated_poms: Dict[str, Path] = {}

    @staticmethod
    def check_maven_availability() -> bool:
        """Check if Maven is available on the system.

        Returns:
            bool: True if Maven is available and working, False otherwise
        """
        try:
            result = subprocess.run(
                ["mvn", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=10,
            )

            if result.returncode == 0:
                try:
                    maven_version = result.stdout.split()[2]
                    logger.info(f"Maven available: {maven_version}")
                except (IndexError, AttributeError):
                    logger.info(
                        "Maven available, but version could not be determined from output."
                    )
                return True
            else:
                logger.warning(f"Maven check failed: {result.stderr}")
                return False

        except FileNotFoundError:
            logger.warning("Maven not found on the system.")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Maven availability check timed out.")
            return False
        except Exception as e:
            logger.warning(f"Error checking Maven availability: {str(e)}")
            return False

    @staticmethod
    def generate_effective_pom(
        workspace: Path,
        profiles: List[str],
        output_file: Optional[Path] = None,
    ) -> Path:
        """Generate an effective POM for the given profiles.

        This method runs `mvn help:effective-pom` to resolve all inheritance,
        property references, and profile activations into a single effective POM.

        Args:
            workspace: Path to the Maven project directory (containing pom.xml)
            profiles: List of profile IDs to activate (e.g., ['azure', 'aws'])
            output_file: Optional path for output file. If None, creates temp file.

        Returns:
            Path: Path to the generated effective POM file

        Raises:
            ResourceError: If Maven execution fails or workspace is invalid
        """
        # Validate workspace
        workspace_path = Path(workspace)
        if not workspace_path.exists():
            raise ResourceError(f"Workspace directory does not exist: {workspace}")

        pom_file = workspace_path / "pom.xml"
        if not pom_file.exists():
            raise ResourceError(f"No pom.xml found in workspace: {workspace}")

        # Create output file if not provided
        if output_file is None:
            profile_suffix = "-".join(profiles) if profiles else "default"
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=f"-{profile_suffix}.xml",
                prefix="effective-pom-",
                delete=False,
            )
            output_file = Path(temp_file.name)
            temp_file.close()

        # Build Maven command
        maven_cmd = [
            "mvn",
            "help:effective-pom",
            "-f",
            str(pom_file),
            f"-Doutput={output_file}",
        ]

        # Add profiles if specified
        if profiles:
            maven_cmd.append(f"-P{','.join(profiles)}")

        logger.info(f"Generating effective POM with command: {' '.join(maven_cmd)}")

        try:
            # Execute Maven command
            result = subprocess.run(
                maven_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=60,  # 60 second timeout
                cwd=str(workspace_path),
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Maven effective-pom failed: {error_msg}")

                # Check for specific error patterns
                if "Unknown lifecycle phase" in error_msg:
                    raise ResourceError("Maven help:effective-pom plugin not available")
                elif "Non-resolvable parent POM" in error_msg:
                    raise ResourceError(
                        "Cannot resolve parent POM - check repositories"
                    )
                elif "Unknown profile" in error_msg:
                    raise ResourceError(
                        f"Unknown profile specified: {profiles}. "
                        "Check available profiles in pom.xml"
                    )
                else:
                    raise ResourceError(
                        f"Maven effective-pom generation failed: {error_msg[:500]}"
                    )

            # Verify output file was created
            if not output_file.exists():
                raise ResourceError(
                    "Maven completed but effective POM file was not created"
                )

            # Verify output file has content
            if output_file.stat().st_size == 0:
                raise ResourceError("Maven generated empty effective POM file")

            logger.info(
                f"Successfully generated effective POM: {output_file} "
                f"({output_file.stat().st_size} bytes)"
            )

            return output_file

        except subprocess.TimeoutExpired:
            logger.error("Maven effective-pom command timed out")
            raise ResourceError(
                "Maven effective-pom generation timed out after 60 seconds"
            )
        except Exception as e:
            if isinstance(e, ResourceError):
                raise
            logger.error(f"Error generating effective POM: {str(e)}")
            raise ResourceError(f"Error generating effective POM: {str(e)}")

    @staticmethod
    def generate_effective_poms_for_profiles(
        workspace: Path, profiles: List[str]
    ) -> Dict[str, Path]:
        """Generate effective POMs for each profile separately.

        This is useful when you need to scan each profile independently
        to identify profile-specific dependencies and vulnerabilities.

        Args:
            workspace: Path to the Maven project directory
            profiles: List of profile IDs to process

        Returns:
            Dict mapping profile ID to effective POM path

        Raises:
            ResourceError: If Maven execution fails for any profile
        """
        effective_poms = {}
        failed_profiles = []

        for profile in profiles:
            try:
                logger.info(f"Generating effective POM for profile: {profile}")
                effective_pom = MavenEffectivePomService.generate_effective_pom(
                    workspace, [profile]
                )
                effective_poms[profile] = effective_pom

            except ResourceError as e:
                logger.error(
                    f"Failed to generate effective POM for profile '{profile}': {str(e)}"
                )
                failed_profiles.append((profile, str(e)))

        # If any profiles failed, raise error with details
        if failed_profiles:
            error_details = "; ".join(
                [f"{prof}: {err}" for prof, err in failed_profiles]
            )
            raise ResourceError(
                f"Failed to generate effective POMs for profiles: {error_details}"
            )

        logger.info(
            f"Successfully generated {len(effective_poms)} effective POMs for profiles: "
            f"{', '.join(effective_poms.keys())}"
        )

        # Store generated POMs for later cleanup
        MavenEffectivePomService._generated_poms = effective_poms

        return effective_poms

    @staticmethod
    def cleanup_effective_poms(
        effective_poms: Optional[Dict[str, Path]] = None,
    ) -> None:
        """Clean up temporary effective POM files.

        Args:
            effective_poms: Dict mapping profile ID to effective POM path.
                          If None, uses stored POMs from generation.
        """
        # Use provided poms or fall back to stored poms
        poms_to_cleanup = effective_poms or MavenEffectivePomService._generated_poms

        for profile, pom_path in poms_to_cleanup.items():
            try:
                if pom_path.exists():
                    pom_path.unlink()
                    logger.debug(
                        f"Cleaned up effective POM for profile '{profile}': {pom_path}"
                    )
            except Exception as e:
                logger.warning(f"Failed to cleanup effective POM {pom_path}: {str(e)}")

        # Clear the stored POMs after cleanup if no explicit poms were provided
        if effective_poms is None:
            MavenEffectivePomService._generated_poms = {}
