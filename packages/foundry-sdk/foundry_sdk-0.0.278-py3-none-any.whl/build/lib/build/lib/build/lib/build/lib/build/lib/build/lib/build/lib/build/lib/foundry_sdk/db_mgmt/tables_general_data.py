import typing as t

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Companies(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, Identity(always=True), primary_key=True)  # IDENTITY autoincrement
    name = Column(Text, nullable=False, unique=True)
    frequency = Column(Integer, nullable=False)

    dataset_type = Column(Text, nullable=False)
    min_date = Column(Date, nullable=False)
    max_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)

    __unique_keys__: t.ClassVar[list[str]] = ["name"]


class Regions(Base):
    __tablename__ = "regions"

    region_id = Column(Integer, Identity(always=True), primary_key=True)  # IDENTITY autoincrement
    abbreviation = Column(Text, nullable=False)
    type = Column(Text, nullable=False)  # consider: region_type
    country = Column(Integer, nullable=False)

    name = Column(Text, nullable=False)
    parent_region_id = Column(
        Integer,
        ForeignKey("regions.region_id", name="link_to_parent_regions", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("abbreviation", "type", "country"),
        Index("unique_region_index", "parent_region_id", "name", "abbreviation", "type", unique=True),
        Index("unique_top_level_regions", "name", "abbreviation", "type", unique=True),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["abbreviation", "type", "country"]
