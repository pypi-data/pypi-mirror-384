import enum
import typing as t

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# TimescaleDB Constants
TIMESCALE_NUMBER_PARTITIONS = 32
TIMESCALE_REGION_PARTITIONS = 16  # Regions often have lower cardinality
TIMESCALE_CHUNK_INTERVAL = "14 days"
TIMESCALE_COMPRESS_AFTER = "30 days"


class Companies(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True)  # IDENTITY handled by overarching database
    name = Column(Text, nullable=False, unique=True)
    frequency = Column(Integer, nullable=False)

    dataset_type = Column(Text, nullable=False)
    min_date = Column(Date, nullable=False)
    max_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)

    __unique_keys__: t.ClassVar[list[str]] = ["name"]


class DatasetType(enum.Enum):
    train = "train"
    val = "val"
    test = "test"


class Datasets(Base):
    __tablename__ = "datasets"

    dataset_id = Column(Integer, Identity(always=True), primary_key=True)
    primary_type = Column(Enum(DatasetType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    __unique_keys__: t.ClassVar[list[str]] = ["name"]


class DatasetMappingTrain(Base):
    __tablename__ = "dataset_mapping_train"

    dataset_id = Column(
        Integer,
        ForeignKey(
            "datasets.dataset_id", name="fk_dataset_mapping_train_datasets", onupdate="RESTRICT", ondelete="CASCADE"
        ),
        nullable=False,
    )

    company_id = Column(
        Integer,
        nullable=False,
    )

    sku_id = Column(
        Integer,
        nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint("dataset_id", "sku_id", "company_id", name="pk_dataset_mapping_train"),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.company_id"],
            name="fk_dataset_mapping_train_companies",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_dataset_mapping_train_sku_table",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["dataset_id", "company_id", "sku_id"]


class SKUType(enum.Enum):
    known_sku = "known_sku"
    unknown_sku = "unknown_sku"
    unknown_store = "unknown_store"
    unknown_product = "unknown_product"
    unknown_company = "unknown_company"


class DatasetMappingTestVal(Base):
    __tablename__ = "dataset_mapping_test_val"

    dataset_id = Column(
        Integer,
        ForeignKey(
            "datasets.dataset_id", name="fk_dataset_mapping_test_val_datasets", onupdate="RESTRICT", ondelete="CASCADE"
        ),
        nullable=False,
    )

    company_id = Column(
        Integer,
        nullable=False,
    )

    sku_id = Column(
        Integer,
        nullable=False,
    )

    sku_type = Column(
        Enum(SKUType),
        nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint("dataset_id", "sku_id", "company_id", name="pk_dataset_mapping_test_val"),
        ForeignKeyConstraint(
            ["company_id"],
            ["companies.company_id"],
            name="fk_dataset_mapping_test_val_companies",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_dataset_mapping_test_val_sku_table",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["dataset_id", "company_id", "sku_id"]



class Regions(Base):
    __tablename__ = "regions"

    region_id = Column(Integer, primary_key=True)  # IDENTITY handled by overarching database
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


class Stores(Base):
    __tablename__ = "stores"

    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", name="link_to_companies", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )
    store_id = Column(Integer, Identity(always=True))
    region_id = Column(
        Integer,
        ForeignKey("regions.region_id", name="link_to_regions", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(Text, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "store_id", name="pk_stores"),
        UniqueConstraint("company_id", "name"),
        Index("ix_stores_company_id", "company_id"),
        Index("ix_stores_region_id", "region_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "name"]


class Categories(Base):
    __tablename__ = "categories"

    # Columns
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", name="fk_categories_companies", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )
    category_id = Column(Integer, Identity(always=True), nullable=False)
    name = Column(Text, nullable=False)

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "category_id", name="pk_categories"),
        UniqueConstraint("company_id", "name", name="uq_categories_company_name"),
        Index("ix_categories_company_id", "company_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "name"]


class CategoryLevelDescriptions(Base):
    __tablename__ = "category_level_descriptions"

    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", name="fk_catleveldesc_companies", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )
    level_id = Column(Integer, Identity(always=True), nullable=False)
    level = Column(Integer, nullable=False)
    name = Column(Text, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "level_id", name="pk_category_level_descriptions"),
        UniqueConstraint("company_id", "level", "name", name="uq_catleveldesc_company_level_name"),
        Index("ix_catleveldesc_company_id", "company_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "level", "name"]


class CategoryRelations(Base):
    __tablename__ = "category_relations"

    # Columns
    company_id = Column(
        Integer,
        ForeignKey(
            "companies.company_id", name="fk_category_relations_companies", onupdate="RESTRICT", ondelete="CASCADE"
        ),
        nullable=False,
    )
    sub_category_id = Column(
        Integer,
        nullable=False,
    )
    parent_category_id = Column(
        Integer,
        nullable=False,
    )

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sub_category_id", "parent_category_id", name="pk_category_relations"),
        ForeignKeyConstraint(
            ["company_id", "sub_category_id"],
            ["categories.company_id", "categories.category_id"],
            name="fk_category_relations_sub",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "parent_category_id"],
            ["categories.company_id", "categories.category_id"],
            name="fk_category_relations_parent",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        UniqueConstraint("company_id", "sub_category_id", "parent_category_id"),
        Index("ix_category_relations_company_id", "company_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sub_category_id", "parent_category_id"]


class Products(Base):
    __tablename__ = "products"

    # Columns
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", name="fk_products_companies", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )
    product_id = Column(Integer, Identity(always=True), nullable=False)
    name = Column(Text, nullable=False)

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "product_id", name="pk_products"),
        UniqueConstraint("company_id", "name", name="uq_products_company_name"),
        Index("ix_products_company_id", "company_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "name"]


class ProductCategories(Base):
    __tablename__ = "product_categories"

    # Columns
    company_id = Column(
        Integer,
        nullable=False,
    )
    product_id = Column(
        Integer,
        nullable=False,
    )
    category_id = Column(
        Integer,
        nullable=False,
    )

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "product_id", "category_id", name="pk_product_categories"),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.product_id"],
            name="fk_product_categories_products",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "category_id"],
            ["categories.company_id", "categories.category_id"],
            name="fk_product_categories_categories",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        UniqueConstraint("company_id", "product_id", "category_id"),
        Index("ix_product_categories_company_id", "company_id"),
        Index("ix_product_categories_product_id", "company_id", "product_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "product_id", "category_id"]


class SkuTable(Base):
    __tablename__ = "sku_table"

    # Columns
    company_id = Column(
        Integer,
        nullable=False,
    )
    sku_id = Column(Integer, Identity(always=True), nullable=False)
    product_id = Column(
        Integer,
        nullable=False,
    )
    store_id = Column(
        Integer,
        nullable=False,
    )

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", name="pk_sku_table"),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.product_id"],
            name="fk_sku_table_products",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "store_id"],
            ["stores.company_id", "stores.store_id"],
            name="fk_sku_table_stores",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        UniqueConstraint("company_id", "product_id", "store_id"),
        Index("ix_sku_table_company_id", "company_id"),
        Index("ix_sku_table_sku_id", "company_id", "sku_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "product_id", "store_id"]


class FeatureDescriptions(Base):
    __tablename__ = "feature_descriptions"

    # Columns
    company_id = Column(
        Integer,
        ForeignKey(
            "companies.company_id", name="fk_feature_descriptions_companies", onupdate="RESTRICT", ondelete="CASCADE"
        ),
        nullable=False,
    )
    feature_id = Column(Integer, Identity(always=True), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    var_type = Column(Text, nullable=False)
    feature_type = Column(Text, nullable=False)

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "feature_id", name="pk_feature_descriptions"),
        UniqueConstraint("company_id", "name", name="uq_feature_descriptions_company_name"),
        Index("ix_feature_descriptions_company_id", "company_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "name"]


class FeatureLevels(Base):
    __tablename__ = "feature_levels"

    # Columns
    company_id = Column(
        Integer,
        nullable=False,
    )
    feature_id = Column(
        Integer,
        nullable=False,
    )
    level = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False)

    # Constraints / Indexes
    __table_args__ = (
        PrimaryKeyConstraint("company_id", "feature_id", "level", name="pk_feature_levels"),
        UniqueConstraint("company_id", "feature_id", "sort_order", name="uq_feature_levels_company_feature_order"),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_feature_levels_feature_descriptions",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_feature_levels_company_feature", "company_id", "feature_id"),
        Index("ix_feature_levels_company_id", "company_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "feature_id", "level"]


class StoreFeatures(Base):
    __tablename__ = "store_features"

    company_id = Column(Integer, nullable=False)
    store_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "store_id", "feature_id", name="pk_store_features"),
        ForeignKeyConstraint(
            ["company_id", "store_id"],
            ["stores.company_id", "stores.store_id"],
            name="fk_store_features_stores",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_store_features_feat",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_store_features_company_store", "company_id", "store_id"),
        Index("ix_store_features_company_feature", "company_id", "feature_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "store_id", "feature_id"]


class StoreFeaturesText(Base):
    __tablename__ = "store_features_text"

    company_id = Column(Integer, nullable=False)
    store_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "store_id", "feature_id", name="pk_store_features_text"),
        ForeignKeyConstraint(
            ["company_id", "store_id"],
            ["stores.company_id", "stores.store_id"],
            name="fk_store_features_text_stores",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_store_features_text_feat",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_store_features_text_company_store", "company_id", "store_id"),
        Index("ix_store_features_text_company_feature", "company_id", "feature_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "store_id", "feature_id"]


class ProductFeatures(Base):
    __tablename__ = "product_features"

    company_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "product_id", "feature_id", name="pk_product_features"),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.product_id"],
            name="fk_product_features_products",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_product_features_feat",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_product_features_company_product", "company_id", "product_id"),
        Index("ix_product_features_company_feature", "company_id", "feature_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "product_id", "feature_id"]


class ProductFeaturesText(Base):
    __tablename__ = "product_features_text"

    company_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "product_id", "feature_id", name="pk_product_features_text"),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.product_id"],
            name="fk_product_features_text_products",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_product_features_text_feat",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_product_features_text_company_product", "company_id", "product_id"),
        Index("ix_product_features_text_company_feature", "company_id", "feature_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "product_id", "feature_id"]


class SkuFeatures(Base):
    __tablename__ = "sku_features"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", "feature_id", name="pk_sku_features"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_sku_features_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_sku_features_feat",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_sku_features_company_sku", "company_id", "sku_id"),
        Index("ix_sku_features_company_feature", "company_id", "feature_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "feature_id"]


class SkuFeaturesText(Base):
    __tablename__ = "sku_features_text"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", "feature_id", name="pk_sku_features_text"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_sku_features_text_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_sku_features_text_feat",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        Index("ix_sku_features_text_company_sku", "company_id", "sku_id"),
        Index("ix_sku_features_text_company_feature", "company_id", "feature_id"),
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "feature_id"]


class TimeProductFeatures(Base):
    __tablename__ = "time_product_features"

    company_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "product_id", "feature_id", "ts", name="pk_time_product_features"),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.product_id"],
            name="fk_tpf_products",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_tpf_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "product_id",  # spreads mega-tenant across partitions
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "product_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "product_id", "feature_id", "ts"]


class TimeProductFeaturesText(Base):
    __tablename__ = "time_product_features_text"

    company_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "product_id", "feature_id", "ts", name="pk_time_product_features_text"),
        ForeignKeyConstraint(
            ["company_id", "product_id"],
            ["products.company_id", "products.product_id"],
            name="fk_tpf_text_products",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_tpf_text_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "product_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "product_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "product_id", "feature_id", "ts"]


class TimeRegionFeatures(Base):
    __tablename__ = "time_region_features"

    company_id = Column(Integer, nullable=False)
    region_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "region_id", "feature_id", "ts", name="pk_time_region_features"),
        # If regions are GLOBAL (no company_id on regions):
        ForeignKeyConstraint(
            ["region_id"], ["regions.region_id"], name="fk_trf_regions", onupdate="RESTRICT", ondelete="CASCADE"
        ),
        # If regions are PER-COMPANY, replace the FK above with:
        # ForeignKeyConstraint(
        #     ["company_id", "region_id"], ["regions.company_id", "regions.region_id"],
        #     name="fk_trf_regions", onupdate="RESTRICT", ondelete="CASCADE"
        # ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_trf_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    # Regions often have lower cardinality; keep overrideable.
                    "space_column": "region_id",
                    "number_partitions": TIMESCALE_REGION_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "region_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "region_id", "feature_id", "ts"]


class TimeRegionFeaturesText(Base):
    __tablename__ = "time_region_features_text"

    company_id = Column(Integer, nullable=False)
    region_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "region_id", "feature_id", "ts", name="pk_time_region_features_text"),
        ForeignKeyConstraint(
            ["region_id"], ["regions.region_id"], name="fk_trf_text_regions", onupdate="RESTRICT", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_trf_text_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "region_id",
                    "number_partitions": TIMESCALE_REGION_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "region_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "region_id", "feature_id", "ts"]


class TimeStoreFeatures(Base):
    __tablename__ = "time_store_features"

    # keys
    company_id = Column(Integer, nullable=False)
    store_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)

    # time + value
    ts = Column(Date, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "store_id", "feature_id", "ts", name="pk_time_store_features"),
        # composite FKs
        ForeignKeyConstraint(
            ["company_id", "store_id"],
            ["stores.company_id", "stores.store_id"],
            name="fk_tsf_stores",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_tsf_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        # covering indexes
        # Timescale metadata for your migrations/agent
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "store_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "store_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "store_id", "feature_id", "ts"]


class TimeStoreFeaturesText(Base):
    __tablename__ = "time_store_features_text"

    # keys
    company_id = Column(Integer, nullable=False)
    store_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)

    # time + value
    ts = Column(Date, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "store_id", "feature_id", "ts", name="pk_time_store_features_text"),
        # composite FKs
        ForeignKeyConstraint(
            ["company_id", "store_id"],
            ["stores.company_id", "stores.store_id"],
            name="fk_tsf_text_stores",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_tsf_text_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        # Timescale metadata for your migrations/agent
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "store_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "store_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "store_id", "feature_id", "ts"]


class TimeSkuFeatures(Base):
    __tablename__ = "time_sku_features"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(DOUBLE_PRECISION)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", "feature_id", "ts", name="pk_time_sku_features"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_tskuf_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_tskuf_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "sku_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "sku_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "feature_id", "ts"]


class Flags(Base):
    __tablename__ = "flags"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(Boolean)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", "feature_id", "ts", name="pk_flags"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_flags_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_flags_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "sku_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "sku_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "feature_id", "ts"]


class TimeSkuFeaturesText(Base):
    __tablename__ = "time_sku_features_text"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    feature_id = Column(Integer, nullable=False)
    ts = Column(Date, nullable=False)
    value = Column(Text)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", "feature_id", "ts", name="pk_time_sku_features_text"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_tskuf_text_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["company_id", "feature_id"],
            ["feature_descriptions.company_id", "feature_descriptions.feature_id"],
            name="fk_tskuf_text_features",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "ts",
                    "space_column": "sku_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "sku_id", "feature_id"],
                        "orderby": "ts DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "feature_id", "ts"]


class OrderIntake(Base):
    """
    Aggregated intake per (order_date, expected_delivery_date) for each SKU.
    Hypertable partitioned by order_date (time) + space partition by sku_id.
    Grain: one row per (company_id, sku_id, order_date, expected_delivery_date) with summed quantity.
    """

    __tablename__ = "order_intake"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False)  # time column (bucketed to day)
    expected_delivery_date = Column(Date, nullable=False)  # expected_delivery_date
    quantity = Column(DOUBLE_PRECISION, nullable=False)

    __table_args__ = (
        # PK includes time (order_date) and space (sku_id) to satisfy Timescale uniqueness rules
        PrimaryKeyConstraint("company_id", "sku_id", "order_date", "expected_delivery_date", name="pk_order_intake"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_oid_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "order_date",
                    "space_column": "sku_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "sku_id"],
                        "orderby": "order_date DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "order_date", "expected_delivery_date"]


class ExpectedDeliveries(Base):
    """
    Final realized demand totals per (sku, expected_delivery_date).
    Hypertable partitioned by expected_delivery_date (time) + space partition by sku_id.
    Maintained via small ETL upserts from order_intake.
    """

    __tablename__ = "expected_deliveries"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    expected_delivery_date = Column(Date, nullable=False)  # time column
    quantity = Column(DOUBLE_PRECISION, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "sku_id", "expected_delivery_date", name="pk_expected_deliveries"),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_dbd_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "expected_delivery_date",
                    "space_column": "sku_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "sku_id"],
                        "orderby": "expected_delivery_date DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "expected_delivery_date"]


class ChangeLogCommitted(Base):
    """
    SCD-2 change log of committed quantities (as-of features).
    Hypertable partitioned by valid_from (time) + space partition by sku_id.
    One row per change of the committed total for each (company, sku, expected_delivery_date).
    """

    __tablename__ = "change_log_committed"

    company_id = Column(Integer, nullable=False)
    sku_id = Column(Integer, nullable=False)
    expected_delivery_date = Column(Date, nullable=False)
    valid_from = Column(Date, nullable=False)  # time column (as-of)
    quantity = Column(DOUBLE_PRECISION, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint(
            "company_id", "sku_id", "expected_delivery_date", "valid_from", name="pk_change_log_committed"
        ),
        ForeignKeyConstraint(
            ["company_id", "sku_id"],
            ["sku_table.company_id", "sku_table.sku_id"],
            name="fk_clc_sku",
            onupdate="RESTRICT",
            ondelete="CASCADE",
        ),
        {
            "info": {
                "timescale": {
                    "time_column": "valid_from",
                    "space_column": "sku_id",
                    "number_partitions": TIMESCALE_NUMBER_PARTITIONS,
                    "chunk_interval": TIMESCALE_CHUNK_INTERVAL,
                    "compression": {
                        "enabled": True,
                        "segmentby": ["company_id", "sku_id", "expected_delivery_date"],
                        "orderby": "valid_from DESC",
                        "compress_after": TIMESCALE_COMPRESS_AFTER,
                    },
                    "caggs": [],
                }
            }
        },
    )

    __unique_keys__: t.ClassVar[list[str]] = ["company_id", "sku_id", "expected_delivery_date", "valid_from"]
