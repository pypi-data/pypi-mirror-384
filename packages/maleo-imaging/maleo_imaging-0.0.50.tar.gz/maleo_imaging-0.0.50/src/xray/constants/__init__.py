from maleo.schemas.resource import Resource, ResourceIdentifier
from maleo.types.string import SeqOfStrs


XRAY_RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="xray", name="X-Ray", slug="xray")],
    details=None,
)


VALID_EXTENSIONS: SeqOfStrs = [
    ".dcm",
    ".dicom",
    ".jpeg",
    ".jpg",
    ".png",
]


VALID_MIME_TYPES: SeqOfStrs = [
    "application/dcm",
    "application/dicom",
    "image/jpeg",
    "image/jpg",
    "image/png",
]
