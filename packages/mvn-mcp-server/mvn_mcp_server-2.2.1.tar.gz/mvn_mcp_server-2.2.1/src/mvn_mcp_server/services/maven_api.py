"""Maven API service for mvn MCP Server.

This module provides a unified approach to interacting with the Maven
Central repository API, with caching to reduce redundant requests.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple

import requests
from fastmcp.exceptions import ResourceError

from mvn_mcp_server.shared.data_types import ErrorCode
from mvn_mcp_server.services.cache import MavenCache

# Set up logging
logger = logging.getLogger("mvn-mcp-server")


class MavenApiService:
    """Service for interacting with Maven Central repository.

    This service provides a unified interface for all Maven Central API
    operations, with built-in caching to reduce redundant requests.
    """

    def __init__(self, cache: Optional[MavenCache] = None):
        """Initialize the Maven API service.

        Args:
            cache: Optional MavenCache instance. If not provided,
                  a new cache will be created.
        """
        self.cache = cache or MavenCache()
        self.timeout = 10  # Default timeout in seconds

    def fetch_artifact_metadata(
        self, group_id: str, artifact_id: str
    ) -> Dict[str, Any]:
        """Fetch Maven metadata for an artifact.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID

        Returns:
            Dictionary containing parsed metadata

        Raises:
            ResourceError: If there's an issue with the Maven Central API
        """
        # Convert group ID dots to slashes for repository path
        group_path = group_id.replace(".", "/")
        metadata_url = f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/maven-metadata.xml"

        # Try to get from cache first
        cache_key = f"metadata:{group_id}:{artifact_id}"
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Using cached metadata for {group_id}:{artifact_id}")
            return cached_data

        logger.debug(
            f"Fetching metadata for {group_id}:{artifact_id} from {metadata_url}"
        )

        try:
            response = requests.get(metadata_url, timeout=self.timeout)

            # If metadata doesn't exist, the dependency might not exist at all
            if response.status_code == 404:
                details = {"error_code": ErrorCode.DEPENDENCY_NOT_FOUND}
                raise ResourceError(
                    f"Dependency {group_id}:{artifact_id} not found in Maven Central",
                    details,
                )

            # Check for successful response
            response.raise_for_status()

            # Parse the XML response
            xml_content = response.text

            try:
                root = ET.fromstring(xml_content)

                # Extract metadata
                metadata = {
                    "group_id": root.findtext("./groupId") or group_id,
                    "artifact_id": root.findtext("./artifactId") or artifact_id,
                    "latest_version": root.findtext("./versioning/latest"),
                    "release_version": root.findtext("./versioning/release"),
                    "versions": [],
                }

                # Extract available versions
                for version_element in root.findall(".//version"):
                    if version_element.text:
                        metadata["versions"].append(version_element.text)

                # Cache the result (TTL: 1 hour)
                self.cache.set(cache_key, metadata, ttl=3600)

                return metadata

            except ET.ParseError:
                raise ResourceError(
                    "Failed to parse Maven metadata XML",
                    {"error_code": ErrorCode.MAVEN_API_ERROR},
                )

        except requests.RequestException as e:
            # Handle network errors or non-200 responses
            raise ResourceError(
                f"Error fetching Maven metadata: {str(e)}",
                {"error_code": ErrorCode.MAVEN_API_ERROR},
            )

    def check_artifact_exists(
        self,
        group_id: str,
        artifact_id: str,
        version: str,
        packaging: str = "jar",
        classifier: Optional[str] = None,
    ) -> bool:
        """Check if a specific artifact exists in Maven Central.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID
            version: Artifact version
            packaging: Packaging type (jar, war, etc.)
            classifier: Optional classifier

        Returns:
            Boolean indicating if the artifact exists
        """
        # Convert group ID dots to slashes for repository path
        group_path = group_id.replace(".", "/")

        # Build the URL for the direct repository check
        base_url = (
            f"https://repo1.maven.org/maven2/{group_path}/{artifact_id}/{version}/"
        )
        file_name = f"{artifact_id}-{version}"

        if classifier:
            file_name += f"-{classifier}"

        file_name += f".{packaging}"
        file_url = base_url + file_name

        # Check cache first
        cache_key = f"artifact_exists:{group_id}:{artifact_id}:{version}:{packaging}:{classifier}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached existence check for {file_url}")
            return cached_result

        logger.debug(f"Checking if artifact exists at {file_url}")

        # Check if the file exists using a HEAD request
        try:
            response = requests.head(file_url, timeout=self.timeout)

            # If we get a 200 OK, the file exists
            if response.status_code == 200:
                self.cache.set(cache_key, True, ttl=3600)  # Cache for 1 hour
                return True

            # If the direct file check failed, try the Maven metadata approach
            if response.status_code == 404:
                exists = self._check_version_in_metadata(group_id, artifact_id, version)
                self.cache.set(cache_key, exists, ttl=3600)  # Cache for 1 hour
                return exists

            # For other status codes, raise an error
            response.raise_for_status()

        except requests.RequestException as e:
            # Log the error but don't fail the check
            logger.warning(f"Error checking artifact existence: {str(e)}")

        # Default fallback
        return False

    def _check_version_in_metadata(
        self, group_id: str, artifact_id: str, version: str
    ) -> bool:
        """Check if a version is listed in the Maven metadata.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID
            version: Version to check

        Returns:
            Boolean indicating if the version is listed in metadata
        """
        try:
            # Fetch metadata
            metadata = self.fetch_artifact_metadata(group_id, artifact_id)

            # Check if version exists in versions list
            return version in metadata["versions"]

        except ResourceError:
            return False

    def get_all_versions(self, group_id: str, artifact_id: str) -> List[str]:
        """Get all available versions for a Maven artifact.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID

        Returns:
            List of version strings

        Raises:
            ResourceError: If there's an issue with the Maven Central API
        """
        try:
            # Fetch metadata (which includes versions)
            metadata = self.fetch_artifact_metadata(group_id, artifact_id)

            # Check if we have any versions
            if not metadata["versions"]:
                raise ResourceError(
                    f"No versions found for {group_id}:{artifact_id}",
                    {"error_code": ErrorCode.DEPENDENCY_NOT_FOUND},
                )

            return metadata["versions"]

        except ResourceError as e:
            # Try fallback to Solr API
            logger.debug(
                f"Metadata approach failed, trying Solr API fallback: {str(e)}"
            )
            return self._get_versions_from_solr(group_id, artifact_id)

    def _get_versions_from_solr(self, group_id: str, artifact_id: str) -> List[str]:
        """Get versions using the Solr search API as a fallback.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID

        Returns:
            List of version strings

        Raises:
            ResourceError: If there's an issue with the Maven Central API
        """
        # Build the query for Maven Central
        query = f"g:{group_id} AND a:{artifact_id}"

        # Check cache first
        cache_key = f"solr_versions:{group_id}:{artifact_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached Solr versions for {group_id}:{artifact_id}")
            return cached_result

        # Make the query
        try:
            response_data, error = self.search_artifacts(query, rows=100)

            if error:
                raise ResourceError(
                    f"Error searching Maven Central: {error}",
                    {"error_code": ErrorCode.MAVEN_API_ERROR},
                )

            # Extract versions
            docs = response_data.get("response", {}).get("docs", [])
            if not docs:
                raise ResourceError(
                    f"No results found for {group_id}:{artifact_id}",
                    {"error_code": ErrorCode.DEPENDENCY_NOT_FOUND},
                )

            versions = []
            for doc in docs:
                version = doc.get("v")
                if version:
                    versions.append(version)

            if not versions:
                raise ResourceError(
                    f"No versions found for {group_id}:{artifact_id}",
                    {"error_code": ErrorCode.DEPENDENCY_NOT_FOUND},
                )

            # Cache the result (TTL: 1 hour)
            self.cache.set(cache_key, versions, ttl=3600)

            return versions

        except Exception as e:
            raise ResourceError(
                f"Failed to get versions via Solr API: {str(e)}",
                {"error_code": ErrorCode.MAVEN_API_ERROR},
            )

    def search_artifacts(
        self,
        query: str,
        packaging: Optional[str] = None,
        classifier: Optional[str] = None,
        rows: int = 20,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Search Maven Central for artifacts using the Solr API.

        Args:
            query: Solr query string
            packaging: Optional packaging filter
            classifier: Optional classifier filter
            rows: Number of rows to return (default: 20)

        Returns:
            Tuple of (response_data, error) where error is None on success
        """
        # Build the Solr query
        base_url = "https://search.maven.org/solrsearch/select"

        # Add packaging and classifier to query if provided
        full_query = query
        if packaging:
            full_query += f" AND p:{packaging}"
        if classifier:
            full_query += f" AND l:{classifier}"

        params = {
            "q": full_query,
            "rows": rows,
            "wt": "json",
            "core": "gav",  # Use gav core for more precise version searches
        }

        # Check cache first
        cache_key = f"solr_search:{full_query}:{rows}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Using cached Solr search for query: {full_query}")
            return cached_result, None

        logger.debug(f"Searching Maven Central with query: {full_query}")

        try:
            # Make the request to Maven Central
            response = requests.get(base_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Log the response summary
            if "response" in data:
                num_found = data["response"].get("numFound", 0)
                num_docs = len(data["response"].get("docs", []))
                logger.debug(
                    f"Maven Central query returned {num_found} matches, {num_docs} docs in response"
                )

            # Cache the result (TTL: 15 minutes)
            self.cache.set(cache_key, data, ttl=900)

            return data, None

        except requests.RequestException as e:
            logger.error(f"Request error querying Maven Central: {str(e)}")
            return {}, f"Error querying Maven Central: {str(e)}"
        except ValueError as e:
            logger.error(f"Error parsing Maven Central response: {str(e)}")
            return {}, f"Error parsing Maven Central response: {str(e)}"

    def _check_version_with_classifier(
        self,
        group_id: str,
        artifact_id: str,
        version: str,
        packaging: str,
        classifier: str,
    ) -> bool:
        """Check if a specific version exists with the given classifier."""
        return self.check_artifact_exists(
            group_id, artifact_id, version, packaging, classifier
        )

    def _try_release_version(
        self,
        metadata: Dict[str, Any],
        group_id: str,
        artifact_id: str,
        packaging: str,
        classifier: Optional[str],
    ) -> Optional[str]:
        """Try to get the release version if available and compatible."""
        release_version = metadata.get("release_version")
        if not release_version:
            return None

        if classifier:
            if self._check_version_with_classifier(
                group_id, artifact_id, release_version, packaging, classifier
            ):
                return release_version
        else:
            return release_version

        return None

    def _try_latest_version(
        self,
        metadata: Dict[str, Any],
        group_id: str,
        artifact_id: str,
        packaging: str,
        classifier: Optional[str],
    ) -> Optional[str]:
        """Try to get the latest version if available and compatible."""
        latest_version = metadata.get("latest_version")
        if not latest_version:
            return None

        if classifier:
            if self._check_version_with_classifier(
                group_id, artifact_id, latest_version, packaging, classifier
            ):
                return latest_version
        else:
            return latest_version

        return None

    def _find_latest_from_all_versions(
        self,
        metadata: Dict[str, Any],
        group_id: str,
        artifact_id: str,
        packaging: str,
        classifier: Optional[str],
    ) -> Optional[str]:
        """Find the latest version from all available versions."""
        versions = metadata.get("versions")
        if not versions:
            return None

        from mvn_mcp_server.services.version import VersionService

        if classifier:
            # Filter versions that have the classifier
            filtered_versions = [
                version
                for version in versions
                if self._check_version_with_classifier(
                    group_id, artifact_id, version, packaging, classifier
                )
            ]

            if filtered_versions:
                return VersionService.get_latest_version(filtered_versions)
        else:
            return VersionService.get_latest_version(versions)

        return None

    def get_latest_version(
        self,
        group_id: str,
        artifact_id: str,
        packaging: str = "jar",
        classifier: Optional[str] = None,
    ) -> str:
        """Get the latest version of a Maven artifact.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID
            packaging: Packaging type (jar, war, etc.)
            classifier: Optional classifier

        Returns:
            Latest version string

        Raises:
            ResourceError: If there's an issue with the Maven Central API
        """
        try:
            # Fetch metadata
            metadata = self.fetch_artifact_metadata(group_id, artifact_id)

            # Try release version first
            result = self._try_release_version(
                metadata, group_id, artifact_id, packaging, classifier
            )
            if result:
                return result

            # Try latest version
            result = self._try_latest_version(
                metadata, group_id, artifact_id, packaging, classifier
            )
            if result:
                return result

            # Try to find latest from all versions
            result = self._find_latest_from_all_versions(
                metadata, group_id, artifact_id, packaging, classifier
            )
            if result:
                return result

            # If we get here, we couldn't find a suitable version
            raise ResourceError(
                f"No suitable version found for {group_id}:{artifact_id} "
                f"with packaging {packaging} and classifier {classifier}",
                {"error_code": ErrorCode.VERSION_NOT_FOUND},
            )

        except ResourceError:
            # If metadata approach fails, try Solr API
            return self._get_latest_version_from_solr(
                group_id, artifact_id, packaging, classifier
            )

    def _get_latest_version_from_solr(
        self,
        group_id: str,
        artifact_id: str,
        packaging: str = "jar",
        classifier: Optional[str] = None,
    ) -> str:
        """Get latest version using the Solr search API as a fallback.

        Args:
            group_id: Maven group ID
            artifact_id: Maven artifact ID
            packaging: Packaging type
            classifier: Optional classifier

        Returns:
            Latest version string

        Raises:
            ResourceError: If there's an issue with the Maven Central API
        """
        # Get all versions via Solr
        versions = self._get_versions_from_solr(group_id, artifact_id)

        # If we have versions, get the latest
        if versions:
            from mvn_mcp_server.services.version import VersionService

            if classifier:
                # Filter versions that have the classifier
                filtered_versions = []
                for version in versions:
                    version_exists = self.check_artifact_exists(
                        group_id, artifact_id, version, packaging, classifier
                    )
                    if version_exists:
                        filtered_versions.append(version)

                if filtered_versions:
                    return VersionService.get_latest_version(filtered_versions)
                else:
                    raise ResourceError(
                        f"No versions found with classifier {classifier} for {group_id}:{artifact_id}",
                        {"error_code": ErrorCode.VERSION_NOT_FOUND},
                    )
            else:
                return VersionService.get_latest_version(versions)

        # If we get here, we couldn't find any versions
        raise ResourceError(
            f"No versions found for {group_id}:{artifact_id}",
            {"error_code": ErrorCode.DEPENDENCY_NOT_FOUND},
        )
