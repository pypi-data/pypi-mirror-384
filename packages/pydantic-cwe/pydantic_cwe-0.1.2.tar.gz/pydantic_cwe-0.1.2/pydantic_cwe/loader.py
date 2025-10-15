from lxml import etree
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic_cwe.models import Catalog


class Loader:
    def __init__(self, xml_file: str = '~/.pydantic-cwe/cwec_v4.18.xml'):
        """
        Loader for CWE XML files. Parses the XML file and converts it to Pydantic objects.

        Args:
            xml_file (str): Path to the XML file.
        """

        # check if the file exists
        xml_file = Path(xml_file).expanduser()

        if not xml_file.exists():
            raise FileNotFoundError(f"File not found: {xml_file}")

        self.xml_file = xml_file
        self._catalog: Optional[Catalog] = None

    def load(self) -> Catalog:
        """
        Load the XML file and convert it to a WeaknessCatalog object.

        Returns:
            Catalog: The parsed catalog.
        """
        if self._catalog is not None:
            return self._catalog

        # Parse the XML file
        tree = etree.parse(str(self.xml_file))
        root = tree.getroot()

        # Extract namespace
        nsmap = root.nsmap
        ns = nsmap[None] if None in nsmap else ""

        # Convert XML to dict
        xml_dict = self._xml_to_dict(root, ns)

        # Create Catalog from dict
        self._catalog = Catalog.model_validate(xml_dict)

        return self._catalog

    def _xml_to_dict(self, element, namespace: str) -> Dict[str, Any]:
        """
        Convert an XML element to a dictionary.

        Args:
            element: The XML element to convert.
            namespace: The XML namespace.

        Returns:
            Dict[str, Any]: The converted dictionary.
        """
        result = {}

        # Add attributes
        for key, value in element.attrib.items():
            result[key] = value

        # Special case for elements that might contain XML content
        special_xml_content_tags = ["Extended_Description", "Description"]
        tag_name = element.tag

        if namespace and tag_name.startswith('{' + namespace + '}'):
            tag_name = tag_name[len('{' + namespace + '}'):]

        if tag_name in special_xml_content_tags and element.text:
            # For these tags, just return the text content directly
            return element.text.strip()

        # Process child elements
        children_by_tag = {}

        for child in element:
            tag = child.tag
            if namespace and tag.startswith('{' + namespace + '}'):
                tag = tag[len('{' + namespace + '}'):]

            if tag not in children_by_tag:
                children_by_tag[tag] = []

            children_by_tag[tag].append(child)

        # Process each tag
        for tag, children in children_by_tag.items():
            # Special handling for tags that might contain XML content
            if tag in special_xml_content_tags:
                if len(children) == 1:
                    child = children[0]
                    if child.text:
                        result[tag] = child.text.strip()
                    else:
                        result[tag] = ""
                continue

            # If there's only one child with this tag
            if len(children) == 1:
                child = children[0]
                # Handle text content
                if len(child) == 0 and not child.attrib and child.text and child.text.strip():
                    result[tag] = child.text.strip()
                else:
                    # Recursively process child element
                    result[tag] = self._xml_to_dict(child, namespace)
            # If there are multiple children with this tag
            else:
                result[tag] = []
                for child in children:
                    # Handle text content
                    if len(child) == 0 and not child.attrib and child.text and child.text.strip():
                        result[tag].append(child.text.strip())
                    else:
                        # Recursively process child element
                        result[tag].append(self._xml_to_dict(child, namespace))

        return result
