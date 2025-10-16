#!/usr/bin/env python
"""RegScale CLI command to normalize CCI data from XML files."""
import datetime
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

import click

from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import create_progress_object, error_and_exit
from regscale.models.regscale_models import Catalog, SecurityControl, CCI

logger = logging.getLogger("regscale")

# RegScale date format constant
REGSCALE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class CCIImporter:
    """Imports CCI data from XML files and maps to security controls."""

    def __init__(self, xml_data: ET.Element, version: str = "5", verbose: bool = False):
        """
        Initialize the CCI importer.

        :param ET.Element xml_data: The root element of the XML data
        :param str version: NIST version to use for filtering
        :param bool verbose: Whether to output verbose information
        """
        self.xml_data = xml_data
        self.normalized_cci: Dict[str, List[Dict]] = {}
        self.verbose = verbose
        self.reference_version = version
        self._user_context: Optional[Tuple[Optional[str], int]] = None

    @staticmethod
    def _parse_control_id(ref_index: str) -> str:
        """
        Extract the main control_id from a reference index (e.g., 'AC-1 a 1 (b)' -> 'AC-1').

        :param str ref_index: Reference index string to parse
        :return: Main control ID
        :rtype: str
        """
        parts = ref_index.strip().split()
        return parts[0] if parts else ""

    @staticmethod
    def _extract_cci_data(cci_item: ET.Element) -> Tuple[Optional[str], str]:
        """
        Extract CCI ID and definition from CCI item.

        :param ET.Element cci_item: XML element containing CCI data
        :return: Tuple of (cci_id, definition)
        :rtype: Tuple[Optional[str], str]
        """
        cci_id = cci_item.get("id")
        definition_elem = cci_item.find(".//{http://iase.disa.mil/cci}definition")
        definition = definition_elem.text if definition_elem is not None and definition_elem.text else ""
        return cci_id, definition

    def _process_references(self, references: List[ET.Element], cci_id: str, definition: str) -> None:
        """
        Process reference elements and add to normalized CCI data.

        :param List[ET.Element] references: List of reference XML elements
        :param str cci_id: CCI identifier
        :param str definition: CCI definition text
        :rtype: None
        """
        for ref in references:
            if not self._is_valid_reference(ref):
                continue

            ref_index = ref.get("index")
            if ref_index:
                main_control = self._parse_control_id(ref_index)
                self._add_cci_to_control(main_control, cci_id, definition)

    def _is_valid_reference(self, ref: ET.Element) -> bool:
        """
        Check if reference matches the target version.

        :param ET.Element ref: Reference XML element
        :return: True if reference version matches target version
        :rtype: bool
        """
        ref_version = ref.get("version")
        return ref_version is not None and ref_version == self.reference_version

    def _add_cci_to_control(self, main_control: str, cci_id: str, definition: str) -> None:
        """
        Add CCI data to the normalized structure for a control.

        :param str main_control: Control identifier
        :param str cci_id: CCI identifier
        :param str definition: CCI definition
        :rtype: None
        """
        if main_control not in self.normalized_cci:
            self.normalized_cci[main_control] = []
        self.normalized_cci[main_control].append({"cci_id": cci_id, "definition": definition})

    def parse_cci(self) -> None:
        """
        Parse CCI items from XML and normalize them, mapping to parent control only.

        :rtype: None
        """
        if self.verbose:
            logger.info("Parsing CCI items from XML...")

        for cci_item in self.xml_data.findall(".//{http://iase.disa.mil/cci}cci_item"):
            cci_id, definition = self._extract_cci_data(cci_item)
            if not cci_id:
                continue

            references = cci_item.findall(".//{http://iase.disa.mil/cci}reference")
            self._process_references(references, cci_id, definition)

    @staticmethod
    def _get_catalog(catalog_id: int) -> Catalog:
        """
        Get the catalog with specified ID.

        :param int catalog_id: ID of the catalog to retrieve
        :return: Catalog instance
        :rtype: Catalog
        :raises SystemExit: If catalog not found
        """
        try:
            catalog = Catalog.get(id=catalog_id)
            if catalog is None:
                error_and_exit(f"Catalog with id {catalog_id} not found. Please ensure the catalog exists.")
            return catalog
        except Exception:
            error_and_exit(f"Catalog with id {catalog_id} not found. Please ensure the catalog exists.")

    def _get_user_context(self) -> Tuple[Optional[str], int]:
        """
        Get user ID and tenant ID from application config.

        :return: Tuple of (user_id, tenant_id)
        :rtype: Tuple[Optional[str], int]
        """
        if self._user_context is None:
            app = Application()
            user_id = app.config.get("userId")
            tenant_id = app.config.get("tenantId", 1)

            try:
                user_id = str(user_id) if user_id else None
            except (TypeError, ValueError):
                user_id = None
                if self.verbose:
                    logger.warning("userId in config is not set or invalid; created_by will be None.")

            # Convert tenant_id to int if it's a string
            try:
                tenant_id = int(tenant_id)
            except (TypeError, ValueError):
                tenant_id = 1
                if self.verbose:
                    logger.warning("tenantId in config is not valid; using default value 1.")

            self._user_context = (user_id, tenant_id)

        return self._user_context

    @staticmethod
    def _find_existing_cci(control_id: int, cci_id: str) -> Optional[CCI]:
        """
        Find existing CCI by ID within a control.

        :param int control_id: Security control ID
        :param str cci_id: CCI identifier to search for
        :return: Existing CCI instance or None
        :rtype: Optional[CCI]
        """
        try:
            existing_ccis: List[CCI] = CCI.get_all_by_parent(parent_id=control_id)
            for existing in existing_ccis:
                if existing.uuid == cci_id:
                    return existing
        except Exception:
            pass
        return None

    @staticmethod
    def _create_cci_data(
        cci_id: str, definition: str, user_id: Optional[str], tenant_id: int, current_time: str
    ) -> Dict:
        """
        Create common CCI data structure.

        :param str cci_id: CCI identifier
        :param str definition: CCI definition
        :param Optional[str] user_id: User ID
        :param int tenant_id: Tenant ID
        :param str current_time: Current timestamp string
        :return: Dictionary with common CCI attributes
        :rtype: Dict
        """
        return {
            "name": cci_id,
            "description": definition,
            "controlType": "policy",
            "publishDate": current_time,
            "dateLastUpdated": current_time,
            "lastUpdatedById": user_id,
            "isPublic": True,
            "tenantsId": tenant_id,
        }

    @staticmethod
    def _update_existing_cci(existing_cci: CCI, cci_data: Dict) -> None:
        """
        Update an existing CCI with new data.

        :param CCI existing_cci: CCI instance to update
        :param Dict cci_data: Dictionary with CCI attributes
        :rtype: None
        """
        for key, value in cci_data.items():
            setattr(existing_cci, key, value)
        existing_cci.create_or_update()

    @staticmethod
    def _create_new_cci(cci_id: str, cci_data: Dict, control_id: int, user_id: Optional[str], current_time: str) -> CCI:
        """
        Create a new CCI instance.

        :param str cci_id: CCI identifier
        :param Dict cci_data: Dictionary with common CCI attributes
        :param int control_id: Security control ID
        :param Optional[str] user_id: User ID
        :param str current_time: Current timestamp string
        :return: Created CCI instance
        :rtype: CCI
        """
        new_cci = CCI(
            uuid=cci_id,
            securityControlId=control_id,
            createdById=user_id,
            dateCreated=current_time,
            **cci_data,
        )
        new_cci.create()
        return new_cci

    def _process_cci_for_control(
        self, control_id: int, cci_list: List[Dict], user_id: Optional[str], tenant_id: int
    ) -> Tuple[int, int]:
        """
        Process all CCI items for a specific control.

        :param int control_id: Security control ID
        :param List[Dict] cci_list: List of CCI data dictionaries
        :param Optional[str] user_id: User ID
        :param int tenant_id: Tenant ID
        :return: Tuple of (created_count, updated_count)
        :rtype: Tuple[int, int]
        """
        created_count = 0
        updated_count = 0
        current_time = datetime.datetime.now().strftime(REGSCALE_DATE_FORMAT)

        for cci in cci_list:
            cci_id = cci["cci_id"]
            definition = cci["definition"]

            existing_cci = self._find_existing_cci(control_id, cci_id)
            cci_data = self._create_cci_data(cci_id, definition, user_id, tenant_id, current_time)

            if existing_cci:
                self._update_existing_cci(existing_cci, cci_data)
                updated_count += 1
            else:
                self._create_new_cci(cci_id, cci_data, control_id, user_id, current_time)
                created_count += 1

        return created_count, updated_count

    def map_to_security_controls(self, catalog_id: int = 1) -> Dict[str, int]:
        """
        Map normalized CCI data to security controls in the database.

        :param int catalog_id: ID of the catalog containing security controls (default: 1)
        :return: Dictionary with operation statistics
        :rtype: Dict[str, int]
        """
        if self.verbose:
            logger.info("Mapping CCI data to security controls...")

        catalog = self._get_catalog(catalog_id)
        security_controls: List[SecurityControl] = SecurityControl.get_all_by_parent(parent_id=catalog.id)
        control_map = {sc.controlId: sc.id for sc in security_controls}

        user_id, tenant_id = self._get_user_context()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with create_progress_object() as progress:
            logger.info(f"Parsing and mapping {len(self.normalized_cci)} normalized CCI entries...")
            main_task = progress.add_task("Parsing and mapping CCIs...", total=len(self.normalized_cci))
            for main_control, cci_list in self.normalized_cci.items():
                if main_control in control_map:
                    control_id = control_map[main_control]
                    control_created, control_updated = self._process_cci_for_control(
                        control_id, cci_list, user_id, tenant_id
                    )
                    created_count += control_created
                    updated_count += control_updated
                else:
                    skipped_count += len(cci_list)
                    if self.verbose:
                        logger.warning(f"Warning: Control not found for key: {main_control}")
                progress.update(main_task, advance=1)

        return {
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "total_processed": sum(created_count + updated_count + skipped_count),
        }

    def get_normalized_cci(self) -> Dict[str, List[Dict]]:
        """
        Get the normalized CCI data.

        :return: Dictionary of normalized CCI data
        :rtype: Dict[str, List[Dict]]
        """
        return self.normalized_cci


def _load_xml_file(xml_file: str) -> ET.Element:
    """
    Load and parse XML file.

    :param str xml_file: Path to XML file
    :return: Root element of parsed XML
    :rtype: ET.Element
    :raises click.ClickException: If XML parsing fails
    """
    try:
        logger.info(f"Loading XML file: {xml_file}")
        tree = ET.parse(xml_file)
        return tree.getroot()
    except ET.ParseError as e:
        error_and_exit(f"Failed to parse XML file: {e}")


def _display_verbose_output(normalized_data: Dict[str, List[Dict]]) -> None:
    """
    Display detailed normalized CCI data.

    :param Dict[str, List[Dict]] normalized_data: Dictionary of normalized CCI data
    :rtype: None
    """
    logger.info("\nNormalized CCI Data:")
    for key, value in normalized_data.items():
        logger.info(f"  {key}: {len(value)} CCI items")
        for cci in value:
            definition_preview = cci["definition"][:100] + "..." if len(cci["definition"]) > 100 else cci["definition"]
            logger.info(f"    - {cci['cci_id']}: {definition_preview}")


def _display_results(stats: Dict[str, int]) -> None:
    """
    Display database operation results.

    :param Dict[str, int] stats: Dictionary with operation statistics
    :rtype: None
    """
    logger.info(
        f"[green]\nDatabase operations completed:"
        f"[green]\n  - Created: {stats['created']}"
        f"[green]\n  - Updated: {stats['updated']}"
        f"[green]\n  - Skipped: {stats['skipped']}"
        f"[green]\n  - Total processed: {stats['total_processed']}",
    )


def _process_cci_import(importer: CCIImporter, dry_run: bool, verbose: bool, catalog_id: int) -> None:
    """
    Process CCI import with optional database operations.

    :param CCIImporter importer: CCIImporter instance
    :param bool dry_run: Whether to skip database operations
    :param bool verbose: Whether to display verbose output
    :param int catalog_id: ID of the catalog containing security controls
    :rtype: None
    """
    importer.parse_cci()
    normalized_data = importer.get_normalized_cci()

    logger.info(f"[green]Successfully parsed {len(normalized_data)} normalized CCI entries[/green]")

    if verbose:
        _display_verbose_output(normalized_data)

    if not dry_run:
        stats = importer.map_to_security_controls(catalog_id)
        _display_results(stats)
    else:
        logger.info("\n[yellow]DRY RUN MODE: No database changes were made[/yellow]")


@click.command(name="cci_importer")
@click.option(
    "--xml_file", "-f", type=click.Path(exists=True), default=None, required=False, help="Path to the CCI XML file."
)
@click.option("--dry-run", "-d", is_flag=True, help="Parse and display normalized data without saving to database")
@click.option("--verbose", "-v", is_flag=True, help="Display detailed output including all normalized CCI data")
@click.option(
    "--nist-version", "-n", type=click.Choice(["4", "5"]), default="5", help="NIST 800-53 Revision version (default: 5)"
)
@click.option(
    "--catalog-id", "-c", type=click.INT, default=1, help="ID of the catalog containing security controls (default: 1)"
)
def cci_importer(xml_file: str, dry_run: bool, verbose: bool, nist_version: str, catalog_id: int) -> None:
    """Import CCI data from XML files and map to security controls.

    If no XML file is specified, defaults to 'artifacts/U_CCI_List.xml' in the project directory.
    """

    try:
        if not xml_file:
            import importlib.resources as pkg_resources
            from regscale.models import integration_models

            files = pkg_resources.files(integration_models)
            cci_path = files / "CCI_List.xml"
            xml_file = str(cci_path)
        root = _load_xml_file(xml_file)
        importer = CCIImporter(root, version=nist_version, verbose=verbose)
        _process_cci_import(importer, dry_run, verbose, catalog_id)
    except Exception as e:
        error_and_exit(f"Unexpected error: {e}")
