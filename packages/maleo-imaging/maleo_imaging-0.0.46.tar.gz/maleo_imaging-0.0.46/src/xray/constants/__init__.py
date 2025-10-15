from maleo.schemas.resource import Resource, ResourceIdentifier
from maleo.types.string import SequenceOfStrings


XRAY_RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="xray", name="X-Ray", slug="xray")],
    details=None,
)


VALID_EXTENSIONS: SequenceOfStrings = [
    ".dcm",
    ".dicom",
    ".jpeg",
    ".jpg",
    ".png",
]


VALID_MIME_TYPES: SequenceOfStrings = [
    "application/dcm",
    "application/dicom",
    "image/jpeg",
    "image/jpg",
    "image/png",
]
