from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.types import (
    Date,
    Enum,
    Float,
    Integer,
    String,
    Text,
    UUID as SQLAlchemyUUID,
)
from uuid import UUID
from maleo.enums.identity import Gender
from maleo.enums.medical import MedicalService
from maleo.schemas.model import DataIdentifier, DataStatus, DataTimestamp
from maleo.types.any import ListOfAny
from maleo.types.string import OptStr
from maleo.types.uuid import OptUUID
from .enums.inference import InferenceType


class Record(DataTimestamp, DataStatus, DataIdentifier):
    __tablename__ = "xray_records"
    organization_id: Mapped[OptUUID] = mapped_column(
        name="organization_id", type_=SQLAlchemyUUID
    )
    user_id: Mapped[UUID] = mapped_column(
        name="user_id", type_=SQLAlchemyUUID, nullable=False
    )
    medical_service: Mapped[MedicalService] = mapped_column(
        name="medical_service",
        type_=Enum(MedicalService, name="medical_service"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(name="name", type_=String(200), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(
        name="date_of_birth", type_=Date, nullable=False
    )
    gender: Mapped[Gender] = mapped_column(
        name="gender", type_=Enum(Gender, name="gender", nullable=False)
    )
    finding: Mapped[str] = mapped_column(name="finding", type_=Text, nullable=False)
    impression: Mapped[str] = mapped_column(
        name="impression", type_=Text, nullable=False
    )
    recommendation: Mapped[OptStr] = mapped_column(name="recommendation", type_=Text)
    filename: Mapped[str] = mapped_column(name="filename", type_=Text, nullable=False)

    @declared_attr
    def inferences(cls) -> Mapped[list["RecordAndInference"]]:
        return relationship(
            "RecordAndInference",
            back_populates="record",
            cascade="all, delete-orphan",
            order_by="RecordAndInference.id",
        )


class Inference(DataTimestamp, DataStatus, DataIdentifier):
    __tablename__ = "xray_inferences"
    organization_id: Mapped[OptUUID] = mapped_column(
        name="organization_id", type_=SQLAlchemyUUID
    )
    user_id: Mapped[UUID] = mapped_column(
        name="user_id", type_=SQLAlchemyUUID, nullable=False
    )
    medical_service: Mapped[MedicalService] = mapped_column(
        name="medical_service",
        type_=Enum(MedicalService, name="medical_service"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(name="name", type_=String(200), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(
        name="date_of_birth", type_=Date, nullable=False
    )
    gender: Mapped[Gender] = mapped_column(
        name="gender", type_=Enum(Gender, name="gender", nullable=False)
    )
    type: Mapped[InferenceType] = mapped_column(
        name="type", type_=Enum(InferenceType, name="xray_inference_type")
    )
    filename: Mapped[str] = mapped_column(name="filename", type_=Text, nullable=False)
    duration: Mapped[float] = mapped_column(
        name="duration", type_=Float, nullable=False
    )
    output: Mapped[ListOfAny] = mapped_column(
        name="output", type_=JSONB, nullable=False
    )

    @declared_attr
    def records(cls) -> Mapped[list["RecordAndInference"]]:
        return relationship(
            "RecordAndInference",
            back_populates="inference",
            cascade="all, delete-orphan",
            order_by="RecordAndInference.id",
        )


class RecordAndInference(DataTimestamp, DataStatus, DataIdentifier):
    __tablename__ = "xray_record_inferences"
    record_id: Mapped[int] = mapped_column(
        "record_id",
        Integer,
        ForeignKey("xray_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    inference_id: Mapped[int] = mapped_column(
        "inference_id",
        Integer,
        ForeignKey("xray_inferences.id", ondelete="CASCADE"),
        nullable=False,
    )

    @declared_attr
    def record(cls) -> Mapped["Record"]:
        return relationship("Record", back_populates="inferences")

    @declared_attr
    def inference(cls) -> Mapped["Inference"]:
        return relationship("Inference", back_populates="records")
