"""Functions and data for detecting XML file types and subtypes.

Provides utilities to identify XML formats based on MIME types and XML namespaces.
Maps supported subtypes to MIME types and offers helpers for format detection.
"""

from enum import StrEnum
import warnings
from pathlib import Path

from lxml import etree as ET

from .formatinfo import SubType
# pylint: disable=c-extension-no-member

# These are additional MIME Types not contained in MIMETYPES (as returned
# by a detection tool) that are handled as XML files.
XML_MIME_TYPES = [
    "application/xml",
    "text/xml",
]

# Mapping of XML namespaces to SubType
NAMESPACES = {
    "http://datacite.org/schema/kernel-4": SubType.DataCite,
    "http://docbook.org/ns/docbook": SubType.DocBook,
    "http://ead3.archivists.org/schema/": SubType.EAD,
    "http://purl.oclc.org/dsdl/schematron": SubType.Schematron,
    "http://purl.org/dc/elements/1.1/": SubType.DCMI,
    "http://purl.org/rss/1.0/": SubType.RSS,
    "http://relaxng.org/ns/structure/1.0": SubType.RelaxNG,
    "http://schemas.openxmlformats.org/presentationml/2006/main": SubType.PresentationML,
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main": SubType.SpreadsheetML,
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main": SubType.WordprocessingML,
    "http://schemas.xmlsoap.org/soap/envelope/": SubType.SOAP,
    "http://schemas.xmlsoap.org/wsdl/": SubType.WSDL,
    "http://www.collada.org/2005/11/COLLADASchema": SubType.Collada,
    "http://www.lido-schema.org": SubType.LIDO,
    "http://www.loc.gov/MARC21/slim": SubType.MARC21,
    "http://www.loc.gov/METS/": SubType.METS,
    "http://www.loc.gov/mods/v3": SubType.MODS,
    "http://www.loc.gov/premis/rdf/v1#": SubType.PREMIS,
    "http://www.opengis.net/gml": SubType.GML,
    "http://www.opengis.net/kml/2.2": SubType.KML,
    "http://www.tei-c.org/ns/1.0": SubType.TEI,
    "http://www.w3.org/1998/Math/MathML": SubType.MathML,
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": SubType.RDF,
    "http://www.w3.org/1999/XSL/Transform": SubType.XSLT,
    "http://www.w3.org/1999/xhtml": SubType.XHTML,
    "http://www.w3.org/1999/xhtml/vocab#": SubType.XHTML_RDFa,
    "http://www.w3.org/1999/xlink": SubType.Xlink,
    "http://www.w3.org/2000/01/rdf-schema#": SubType.RDFS,
    "http://www.w3.org/2000/SMIL20/": SubType.SMIL,
    "http://www.w3.org/2000/svg": SubType.SVG,
    "http://www.w3.org/2001/SMIL20/Language": SubType.SMIL,
    "http://www.w3.org/2001/XMLSchema": SubType.XSD,
    "http://www.w3.org/2001/vxml": SubType.VoiceXML,
    "http://www.w3.org/2002/07/owl#": SubType.OWL,
    "http://www.w3.org/2002/xforms": SubType.XForms,
    "http://www.w3.org/2005/Atom": SubType.ATOM,
    "http://www.w3.org/XML/1998/namespace": SubType.XML,
    "http://www.web3d.org/specifications/x3d-namespace": SubType.X3D,
    "urn:oasis:names:tc:opendocument:xmlns:office:1.0": SubType.ODF,
}

# Maps SubType values to MIME types for XML formats.
MIMETYPES = {
    SubType.DataCite: "application/datacite+xml",
    SubType.DocBook: "application/docbook+xml",
    SubType.EAD: "application/ead+xml",
    SubType.Schematron: "application/schematron+xml",
    # SubType.DCMI: "application/dcmitype+xml",
    SubType.RSS: "application/rss+xml",
    SubType.RelaxNG: "application/relax-ng+xml",
    SubType.PresentationML: "application/vnd.openxmlformats-officedocument.presentationml",
    SubType.SpreadsheetML: "application/vnd.openxmlformats-officedocument.spreadsheetml",
    SubType.WordprocessingML:  \
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    SubType.SOAP: "application/soap+xml",
    SubType.WSDL: "application/wsdl+xml",
    SubType.Collada: "application/vnd.collada+xml",
    SubType.LIDO: "application/xml",
    SubType.MARC21: "application/marcxml+xml",
    SubType.METS: "application/mets+xml",
    SubType.MODS: "application/mods+xml",
    SubType.PREMIS: "application/rdf+xml",
    SubType.GML: "application/gml+xml",
    SubType.KML: "application/vnd.google-earth.kml+xml",
    SubType.TEI: "application/tei+xml",
    SubType.MathML: "application/mathml+xml",
    SubType.RDF: "application/rdf+xml",
    SubType.XSLT: "application/xslt+xml",
    SubType.XHTML: "application/xhtml+xml",
    SubType.XHTML_RDFa: "application/xhtml+xml",
    SubType.Xlink: "application/xlink+xml",
    SubType.RDFS: "application/rdf+xml",
    SubType.SMIL: "application/smil+xml",
    SubType.SVG: "image/svg+xml",
    SubType.SVG_Animation: "application/smil+xml",
    SubType.XSD: "application/xml",
    SubType.VoiceXML: "application/voicexml+xml",
    SubType.OWL: "application/owl+xml",
    SubType.XForms: "application/xforms+xml",
    SubType.ATOM: "application/atom+xml",
    SubType.XML: "application/xml",
    SubType.X3D: "model/x3d+xml",
    SubType.ODF: "application/vnd.oasis.opendocument.text",
}


def is_xml_type(mimetype: str) -> StrEnum | None:
    """
    Check if a MIME type is recognized as an XML type.

    Args:
        mimetype (str): MIME type to check.

    Returns:
        StrEnum | None: True if the MIME type is a known XML type, otherwise None.
    """
    return mimetype in MIMETYPES.values() or mimetype in XML_MIME_TYPES


def guess_xml_subtype(filepath: Path) -> str:
    """
    Guess the XML subtype of a file by inspecting its namespaces.

    Iterates through the XML file and checks for known namespaces to determine the subtype.
    If the namespace is not recognized, a warning is issued and None is returned.

    Args:
        filepath (Path): Path to the XML file.

    Returns:
        str: SubType value if detected, otherwise None.

    Notes:
        - Useful for simple detectors or exotic formats.
        - Tools like FITS may also detect subtypes, but this function is for custom logic.
    """
    for _, elem in ET.iterparse(filepath, events=["start-ns"]):
        namespace = elem[1]
        try:
            return NAMESPACES[namespace]
        except KeyError:
            warnings.warn(
                f"XML format detection failed due to unknown namespace: {namespace}"
            )
    return None


def get_format_info(filepath: Path, mime_type: str) -> tuple[str, StrEnum | None]:
    """
    Get the format info for an XML file, including fixed MIME type and detected subtype.

    Args:
        filepath (Path): Path to the XML file.
        mime_type (str): MIME type detected by another tool.

    Returns:
        tuple[str, StrEnum | None]: (MIME type, detected subtype) for the file.

    Notes:
        - If the subtype cannot be detected, returns the original MIME type and None.
        - If detected, returns the mapped MIME type and subtype.
    """
    xmltype = guess_xml_subtype(filepath)
    if xmltype is None:
        subtype = None
    else:
        subtype = xmltype
        mime_type = MIMETYPES.get(xmltype, mime_type)
    return mime_type, subtype
