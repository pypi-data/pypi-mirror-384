#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Matcher - A utility class for identifying and matching control implementations
across different RegScale entities based on control ID strings.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Union

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.models.regscale_models.control_implementation import ControlImplementation
from regscale.models.regscale_models.security_control import SecurityControl

logger = logging.getLogger("regscale")


class ControlMatcher:
    """
    A class to identify control IDs and match them across different RegScale entities.

    This class provides control matching capabilities:
    - Parse control ID strings to extract NIST control identifiers
    - Match controls from catalogs to security plans
    - Find control implementations based on control IDs
    - Support multiple control ID formats (e.g., AC-1, AC-1(1), AC-1.1)

    Note: This class is focused on finding and matching existing controls only.
    Control creation/modification should be handled by calling code.
    """

    def __init__(self, app: Optional[Application] = None):
        """
        Initialize the ControlMatcher.

        :param Optional[Application] app: RegScale Application instance
        """
        self.app = app or Application()
        self.api = Api()
        self._catalog_cache: Dict[int, List[SecurityControl]] = {}
        self._control_impl_cache: Dict[Tuple[int, str], Dict[str, ControlImplementation]] = {}

    def parse_control_id(self, control_string: str) -> Optional[str]:
        """
        Parse a control ID string and extract the standardized control identifier.

        Handles various formats:
        - NIST format: AC-1, AC-1(1), AC-1.1
        - With leading zeros: AC-01, AC-17(02)
        - With spaces: AC-1 (1), AC-02 (04)
        - With text: "Access Control AC-1"
        - Multiple controls: "AC-1, AC-2"

        :param str control_string: Raw control ID string
        :return: Standardized control ID or None if not found
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        # Clean the string
        control_string = control_string.strip().upper()

        # Common NIST control ID pattern
        # Matches: AC-1, AC-01, AC-1(1), AC-1(01), AC-1 (1), AC-1.1, AC-1.01, etc.
        # Allows optional whitespace before and inside parentheses
        pattern = r"([A-Z]{2,3}-\d+(?:\s*\(\s*\d+\s*\)|\.\d+)?)"

        matches = re.findall(pattern, control_string)
        if matches:
            # Normalize parentheses to dots for consistency and remove spaces
            control_id = matches[0]
            control_id = control_id.replace(" ", "")  # Remove all spaces
            control_id = control_id.replace("(", ".").replace(")", "")

            # Normalize leading zeros (e.g., AC-01.02 -> AC-1.2)
            parts = control_id.split("-")
            if len(parts) == 2:
                family = parts[0]
                number_part = parts[1]

                if "." in number_part:
                    main_num, enhancement = number_part.split(".", 1)
                    main_num = str(int(main_num))
                    enhancement = str(int(enhancement))
                    control_id = f"{family}-{main_num}.{enhancement}"
                else:
                    main_num = str(int(number_part))
                    control_id = f"{family}-{main_num}"

            return control_id

        return None

    def find_control_in_catalog(self, control_id: str, catalog_id: int) -> Optional[SecurityControl]:
        """
        Find a security control in a specific catalog by control ID.

        :param str control_id: The control ID to search for
        :param int catalog_id: The catalog ID to search in
        :return: SecurityControl object if found, None otherwise
        :rtype: Optional[SecurityControl]
        """
        controls = self._get_catalog_controls(catalog_id)

        # Generate all possible variations of the control ID
        search_ids = self._get_control_id_variations(control_id)

        # Try exact match with any variation
        for control in controls:
            if control.controlId in search_ids:
                return control

        # Try matching control variations against search variations
        for control in controls:
            control_variations = self._get_control_id_variations(control.controlId)
            if control_variations & search_ids:  # Set intersection
                return control

        return None

    def find_control_implementation(
        self, control_id: str, parent_id: int, parent_module: str = "securityplans", catalog_id: Optional[int] = None
    ) -> Optional[ControlImplementation]:
        """
        Find a control implementation based on control ID and parent context.

        :param str control_id: The control ID to match
        :param int parent_id: Parent entity ID (e.g., security plan ID)
        :param str parent_module: Parent module type (default: securityplans)
        :param Optional[int] catalog_id: Optional catalog ID for better matching
        :return: ControlImplementation if found, None otherwise
        :rtype: Optional[ControlImplementation]
        """
        # Get control implementations for the parent
        implementations = self._get_control_implementations(parent_id, parent_module)

        # Get all variations of the control ID for matching
        search_variations = self._get_control_id_variations(control_id)
        if not search_variations:
            logger.warning(f"Could not parse control ID: {control_id}")
            return None

        # Try to find matching implementation with variation matching
        for impl_key, impl in implementations.items():
            impl_variations = self._get_control_id_variations(impl_key)
            if impl_variations & search_variations:  # Set intersection
                return impl

        # If catalog ID provided, try to find via security control
        if catalog_id:
            control = self.find_control_in_catalog(control_id, catalog_id)
            if control:
                # Search implementations by control ID
                for impl in implementations.values():
                    if impl.controlID == control.id:
                        return impl

        return None

    def match_controls_to_implementations(
        self,
        control_ids: List[str],
        parent_id: int,
        parent_module: str = "securityplans",
        catalog_id: Optional[int] = None,
    ) -> Dict[str, Optional[ControlImplementation]]:
        """
        Match multiple control IDs to their implementations.

        :param List[str] control_ids: List of control ID strings
        :param int parent_id: Parent entity ID
        :param str parent_module: Parent module type
        :param Optional[int] catalog_id: Optional catalog ID
        :return: Dictionary mapping control IDs to implementations
        :rtype: Dict[str, Optional[ControlImplementation]]
        """
        results = {}

        for control_id in control_ids:
            impl = self.find_control_implementation(control_id, parent_id, parent_module, catalog_id)
            results[control_id] = impl

        return results

    def get_security_plan_controls(self, security_plan_id: int) -> Dict[str, ControlImplementation]:
        """
        Get all control implementations for a security plan.

        :param int security_plan_id: The security plan ID
        :return: Dictionary of control implementations keyed by control ID
        :rtype: Dict[str, ControlImplementation]
        """
        return self._get_control_implementations(security_plan_id, "securityplans")

    def find_controls_by_pattern(self, pattern: str, catalog_id: int) -> List[SecurityControl]:
        """
        Find all controls in a catalog matching a pattern.

        :param str pattern: Regex pattern or substring to match
        :param int catalog_id: Catalog ID to search in
        :return: List of matching SecurityControl objects
        :rtype: List[SecurityControl]
        """
        controls = self._get_catalog_controls(catalog_id)
        matched = []

        for control in controls:
            if (re.search(pattern, control.controlId, re.IGNORECASE)) or (
                control.title and re.search(pattern, control.title, re.IGNORECASE)
            ):
                matched.append(control)

        return matched

    def bulk_match_controls(
        self,
        control_mappings: Dict[str, str],
        parent_id: int,
        parent_module: str = "securityplans",
        catalog_id: Optional[int] = None,
    ) -> Dict[str, Optional[ControlImplementation]]:
        """
        Bulk match control IDs to their implementations.

        :param Dict[str, str] control_mappings: Dict of {external_id: control_id}
        :param int parent_id: Parent entity ID
        :param str parent_module: Parent module type
        :param Optional[int] catalog_id: Catalog ID for controls
        :return: Dictionary mapping external IDs to ControlImplementations (None if not found)
        :rtype: Dict[str, Optional[ControlImplementation]]
        """
        results = {}

        for external_id, control_id in control_mappings.items():
            impl = self.find_control_implementation(control_id, parent_id, parent_module, catalog_id)
            results[external_id] = impl

        return results

    def _get_catalog_controls(self, catalog_id: int) -> List[SecurityControl]:
        """
        Get all controls for a catalog (with caching).

        :param int catalog_id: Catalog ID
        :return: List of SecurityControl objects
        :rtype: List[SecurityControl]
        """
        if catalog_id not in self._catalog_cache:
            try:
                controls = SecurityControl.get_list_by_catalog(catalog_id)
                self._catalog_cache[catalog_id] = controls
            except Exception as e:
                logger.error(f"Failed to get controls for catalog {catalog_id}: {e}")
                return []

        return self._catalog_cache.get(catalog_id, [])

    def _normalize_control_id(self, control_id: str) -> Optional[str]:
        """
        Normalize a control ID by removing leading zeros from all numeric parts.

        Examples:
        - AC-01 -> AC-1
        - AC-17(02) -> AC-17.2
        - AC-1.01 -> AC-1.1

        :param str control_id: The control ID to normalize
        :return: Normalized control ID or None if invalid
        :rtype: Optional[str]
        """
        parsed = self.parse_control_id(control_id)
        if not parsed:
            return None

        # Split by '-' to get family and number parts
        parts = parsed.split("-")
        if len(parts) != 2:
            return None

        family = parts[0]
        number_part = parts[1]

        # Handle enhancement notation (both . and parentheses are normalized to .)
        if "." in number_part:
            main_num, enhancement = number_part.split(".", 1)
            # Remove leading zeros from both parts
            main_num = str(int(main_num))
            enhancement = str(int(enhancement))
            return f"{family}-{main_num}.{enhancement}"
        else:
            # Just main control number
            main_num = str(int(number_part))
            return f"{family}-{main_num}"

    def _get_control_id_variations(self, control_id: str) -> set:
        """
        Generate all valid variations of a control ID (with and without leading zeros).

        Examples:
        - AC-1 -> {AC-1, AC-01}
        - AC-17.2 -> {AC-17.2, AC-17.02, AC-17(2), AC-17(02)}

        :param str control_id: The control ID to generate variations for
        :return: Set of all valid variations
        :rtype: set
        """
        parsed = self.parse_control_id(control_id)
        if not parsed:
            return set()

        variations = set()

        # Split by '-' to get family and number parts
        parts = parsed.split("-")
        if len(parts) != 2:
            return set()

        family = parts[0]
        number_part = parts[1]

        # Handle enhancement notation
        if "." in number_part:
            main_num, enhancement = number_part.split(".", 1)
            main_int = int(main_num)
            enh_int = int(enhancement)

            # Generate all combinations: with/without leading zeros, dot/parenthesis notation
            for main_fmt in [str(main_int), f"{main_int:02d}"]:
                for enh_fmt in [str(enh_int), f"{enh_int:02d}"]:
                    variations.add(f"{family}-{main_fmt}.{enh_fmt}")
                    variations.add(f"{family}-{main_fmt}({enh_fmt})")
        else:
            # Just main control number
            main_int = int(number_part)
            variations.add(f"{family}-{main_int}")
            variations.add(f"{family}-{main_int:02d}")

        # Add uppercase versions to ensure consistency
        return {v.upper() for v in variations}

    def _get_control_implementations(self, parent_id: int, parent_module: str) -> Dict[str, ControlImplementation]:
        """
        Get control implementations for a parent (with caching).

        :param int parent_id: Parent ID
        :param str parent_module: Parent module
        :return: Dict of implementations keyed by control ID
        :rtype: Dict[str, ControlImplementation]
        """
        cache_key = (parent_id, parent_module)

        if cache_key not in self._control_impl_cache:
            try:
                # Get the label map which maps control IDs to implementation IDs
                label_map = ControlImplementation.get_control_label_map_by_parent(parent_id, parent_module)

                implementations = {}
                for control_label, impl_id in label_map.items():
                    impl = ControlImplementation.get_object(impl_id)
                    if impl:
                        implementations[control_label] = impl

                self._control_impl_cache[cache_key] = implementations
            except Exception as e:
                logger.error(f"Failed to get implementations for {parent_module}/{parent_id}: {e}")
                return {}

        return self._control_impl_cache.get(cache_key, {})

    def clear_cache(self):
        """Clear all cached data."""
        self._catalog_cache.clear()
        self._control_impl_cache.clear()
        logger.info("Cleared control matcher cache")
