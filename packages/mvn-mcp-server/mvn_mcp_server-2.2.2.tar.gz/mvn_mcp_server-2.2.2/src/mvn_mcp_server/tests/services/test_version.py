"""Tests for the version service."""

import unittest
from mvn_mcp_server.services.version import VersionService


class TestVersionService(unittest.TestCase):
    """Test cases for the VersionService class."""

    def test_parse_version_semver(self):
        """Test parsing standard semantic version strings."""
        components, qualifier = VersionService.parse_version("1.2.3")
        self.assertEqual(components, [1, 2, 3])
        self.assertEqual(qualifier, "")

    def test_parse_version_with_qualifier(self):
        """Test parsing version with qualifier."""
        components, qualifier = VersionService.parse_version("1.2.3-SNAPSHOT")
        self.assertEqual(components, [1, 2, 3])
        self.assertEqual(qualifier, "-SNAPSHOT")

        # Test dot-separated qualifier
        components, qualifier = VersionService.parse_version("1.2.3.Final")
        self.assertEqual(components, [1, 2, 3])
        self.assertEqual(qualifier, ".Final")

    def test_parse_version_partial(self):
        """Test parsing partial version strings."""
        # MAJOR.MINOR format
        components, qualifier = VersionService.parse_version("1.2")
        self.assertEqual(components, [1, 2, 0])
        self.assertEqual(qualifier, "")

        # MAJOR only format
        components, qualifier = VersionService.parse_version("5")
        self.assertEqual(components, [5, 0, 0])
        self.assertEqual(qualifier, "")

    def test_parse_version_calendar(self):
        """Test parsing calendar-based version (YYYYMMDD)."""
        components, qualifier = VersionService.parse_version("20231013")
        self.assertEqual(components, [2023, 10, 13])
        self.assertEqual(qualifier, "")

    def test_parse_version_empty(self):
        """Test parsing empty version string."""
        components, qualifier = VersionService.parse_version("")
        self.assertEqual(components, [])
        self.assertEqual(qualifier, "")

    def test_compare_versions_basic(self):
        """Test basic version comparison."""
        self.assertEqual(VersionService.compare_versions("1.2.3", "1.2.3"), 0)
        self.assertEqual(VersionService.compare_versions("1.2.3", "1.2.4"), -1)
        self.assertEqual(VersionService.compare_versions("1.2.3", "1.2.2"), 1)
        self.assertEqual(VersionService.compare_versions("1.3.0", "1.2.9"), 1)
        self.assertEqual(VersionService.compare_versions("2.0.0", "1.9.9"), 1)

    def test_compare_versions_qualifiers(self):
        """Test version comparison with qualifiers."""
        self.assertEqual(VersionService.compare_versions("1.2.3", "1.2.3-SNAPSHOT"), 1)
        self.assertEqual(VersionService.compare_versions("1.2.3-SNAPSHOT", "1.2.3"), -1)
        self.assertEqual(
            VersionService.compare_versions("1.2.3-alpha", "1.2.3-beta"), -1
        )
        self.assertEqual(
            VersionService.compare_versions("1.2.3-beta", "1.2.3-alpha"), 1
        )
        self.assertEqual(VersionService.compare_versions("1.2.3-rc1", "1.2.3-beta2"), 1)
        self.assertEqual(VersionService.compare_versions("1.2.3.Final", "1.2.3"), 1)

    def test_compare_versions_different_lengths(self):
        """Test comparing versions with different component counts."""
        self.assertEqual(VersionService.compare_versions("1.2", "1.2.0"), 0)
        self.assertEqual(VersionService.compare_versions("1.2", "1.2.1"), -1)
        self.assertEqual(VersionService.compare_versions("1.2.0", "1.2"), 0)
        self.assertEqual(VersionService.compare_versions("1", "1.0.0"), 0)

    def test_compare_versions_edge_cases(self):
        """Test edge cases in version comparison."""
        self.assertEqual(VersionService.compare_versions("", ""), 0)
        self.assertEqual(VersionService.compare_versions("1.0.0", ""), 1)
        self.assertEqual(VersionService.compare_versions("", "1.0.0"), -1)

    def test_filter_versions_major(self):
        """Test filtering versions based on major component."""
        versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0", "3.0.0"]
        filtered = VersionService.filter_versions(versions, "major", "1.0.0")
        # For major, all versions should be included
        self.assertEqual(filtered, versions)

    def test_filter_versions_minor(self):
        """Test filtering versions based on minor component."""
        versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0", "3.0.0"]
        filtered = VersionService.filter_versions(versions, "minor", "1.0.0")
        # For minor with reference 1.0.0, only versions with major=1 should be included
        self.assertEqual(filtered, ["1.0.0", "1.1.0", "1.2.0"])

    def test_filter_versions_patch(self):
        """Test filtering versions based on patch component."""
        versions = ["1.0.0", "1.0.1", "1.1.0", "1.1.1", "2.0.0"]
        filtered = VersionService.filter_versions(versions, "patch", "1.0.0")
        # For patch with reference 1.0.0, only versions with major=1, minor=0 should be included
        self.assertEqual(filtered, ["1.0.0", "1.0.1"])

    def test_filter_versions_empty(self):
        """Test filtering an empty list."""
        filtered = VersionService.filter_versions([], "major", "1.0.0")
        self.assertEqual(filtered, [])

    def test_filter_versions_fallback(self):
        """Test filter fallback when no versions match initial criteria."""
        # No versions match patch filter (1.2.x) so it should fall back to minor (1.x)
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        filtered = VersionService.filter_versions(versions, "patch", "1.2.0")
        self.assertEqual(filtered, ["1.0.0", "1.1.0"])

        # No versions match minor filter (3.x) so it should fall back to major (all)
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        filtered = VersionService.filter_versions(versions, "minor", "3.0.0")
        self.assertEqual(filtered, ["1.0.0", "1.1.0", "2.0.0"])

    def test_filter_versions_snapshots(self):
        """Test filtering out SNAPSHOT and pre-release versions."""
        versions = [
            "1.0.0",
            "1.0.0-SNAPSHOT",
            "1.0.0-alpha",
            "1.0.0-beta",
            "1.0.0-rc1",
            "1.0.1",
        ]
        filtered = VersionService.filter_versions(versions, "patch", "1.0.0")
        # Pre-release versions should be filtered out
        self.assertEqual(filtered, ["1.0.0", "1.0.1"])

    def test_get_latest_version_basic(self):
        """Test getting the latest version."""
        versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"]
        latest = VersionService.get_latest_version(versions)
        self.assertEqual(latest, "2.1.0")

    def test_get_latest_version_with_snapshots(self):
        """Test getting latest version with snapshots included/excluded."""
        versions = ["1.0.0", "1.1.0", "1.2.0-SNAPSHOT", "1.2.0"]

        # Without snapshots (default)
        latest = VersionService.get_latest_version(versions)
        self.assertEqual(latest, "1.2.0")

        # With snapshots included
        latest = VersionService.get_latest_version(versions, include_snapshots=True)
        self.assertEqual(latest, "1.2.0")  # Release still higher than snapshot

    def test_get_latest_version_qualifier_order(self):
        """Test latest version with different qualifiers."""
        versions = ["1.0.0-alpha", "1.0.0-beta", "1.0.0-rc1", "1.0.0", "1.0.0.Final"]
        latest = VersionService.get_latest_version(versions)
        self.assertEqual(latest, "1.0.0.Final")  # Final is higher than release

    def test_is_date_based_version(self):
        """Test detection of date-based versions."""
        self.assertTrue(VersionService.is_date_based_version("20231013"))
        self.assertTrue(VersionService.is_date_based_version("20211013"))
        self.assertFalse(VersionService.is_date_based_version("1.2.3"))
        self.assertFalse(VersionService.is_date_based_version("5"))
        self.assertFalse(VersionService.is_date_based_version(""))
        self.assertFalse(
            VersionService.is_date_based_version("12345")
        )  # Not in year range


if __name__ == "__main__":
    unittest.main()
