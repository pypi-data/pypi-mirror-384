import logging
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, timedelta

#### Temporary, potentially to be moved to extra file
from io import BytesIO, StringIO
from uuid import uuid4

import polars as pl
from sqlalchemy import func, or_, select, text
from sqlalchemy.sql import bindparam
from sqlalchemy.ext.declarative import DeclarativeMeta
from tqdm import tqdm

from foundry_sdk.db_mgmt import SQLAlchemyDatabase
from foundry_sdk.db_mgmt.tables_ts import (
    Categories,
    CategoryLevelDescriptions,
    CategoryRelations,
    FeatureDescriptions,
    FeatureLevels,
    Flags,
    OrderIntake,
    ExpectedDeliveries,
    ChangeLogCommitted,
    ProductCategories,
    ProductFeatures,
    ProductFeaturesText,
    Products,
    Regions,
    SkuFeatures,
    SkuFeaturesText,
    SkuTable,
    StoreFeatures,
    StoreFeaturesText,
    Stores,
    TimeProductFeatures,
    TimeProductFeaturesText,
    TimeRegionFeatures,
    TimeRegionFeaturesText,
    TimeSkuFeatures,
    TimeSkuFeaturesText,
    TimeStoreFeatures,
    TimeStoreFeaturesText,
)
from foundry_sdk.db_mgmt.utils.data_retrieval import get_all_dates

from .constants import NUMERIC_VAR_TYPES, TEXT_VAR_TYPES, FlagLevels, TimeDataStrategy
from .etl_utils import get_time_data_strategy, _validate_append_mode

# from foundry_sdk.etl.constants import FlagLevels

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading of data into the database using the write_* methods."""

    def __init__(self, db: SQLAlchemyDatabase, insertion_mode: str) -> None:
        """
        Args:
            db (SQLAlchemyDatabase): Database connection object.
            insertion_mode (InsertionMode): Mode for database insertion.

        """
        # db ignored, is legacy, will be removed from arguments in the future
        self.insertion_mode = insertion_mode
        self.db = db  # to be removed in the future

    #################################### Mandatory data ############################################

    @staticmethod
    def check_check_passed(*, check_passed: bool) -> None:
        if not check_passed:
            raise ValueError("wait for all checks to pass")
    
    def sync_regions(
            self,
    ) -> bool:
        """
        Ensure `regions` in the company DB matches the general masterdata.
        """

        # Open DBs
        general_db = SQLAlchemyDatabase.from_kedro(credentials_name="postgres_general_data")
        company_db = SQLAlchemyDatabase.from_kedro(credentials_name="postgres")

        
        general_df = general_db.copy_read_table(Regions)
        company_df = company_db.copy_read_table(Regions)

        # Case 1: General data empty, raise error
        if general_df.is_empty():
            raise ValueError("General masterdata `regions` is empty")


        # Case 2: Company data not initialized, simple copy
        if company_df.is_empty():
            logger.warning("regions table empty, copying from general masterdata")
            company_db.handle_insertion_multi_line(
                model_class=Regions,
                data=general_df,
                mode=self.insertion_mode,
                returning_id=False,
            )
            logger.info("Inserted %d regions into company DB.", general_df.height)
            return True
        
        # Case 3: Both non-empty, check consistency
        key_cols = list(Regions.__table__.columns.keys())
        # Case 3a: Rows in company not in general, raise error
        company_df = company_df.with_columns(pl.col("parent_region_id").fill_null(-1)) # fill -1 to allow for comparison
        general_df = general_df.with_columns(pl.col("parent_region_id").fill_null(-1)) # fill -1 to allow for comparison
        inconsistent = company_df.join(general_df, on=key_cols, how="anti")
        if not inconsistent.is_empty():
            preview = inconsistent.head(5)
            raise ValueError(
                f"Inconsistent `regions`: {inconsistent.height} row(s) in company DB "
                f"are not in general masterdata. Example(s): {preview}"
            )
        # Case 3b: Rows in general not in company, insert missing
        missing = general_df.join(company_df, on=key_cols, how="anti")
        if missing.is_empty():
            logger.info("`regions` already synchronized (company ⊆ general).")
            return True
        missing = missing.with_columns(pl.col("parent_region_id").replace(-1, None))
        company_db.handle_insertion_multi_line(
            model_class=Regions,
            data=missing,
            mode=self.insertion_mode,
            returning_id=False,
        )
        logger.info("Inserted %d missing regions into company DB.", missing.height)

        return True

       
    def write_company(
        self,
        name: str,
        dataset_type: str,
        description: str,
        min_date: date,
        max_date: date,
        frequency: int,
        *,
        check_passed: bool,
        regions_synced: bool,
    ) -> int:
        """Writes the company metadata to both general and company databases and returns the company ID."""
        DataLoader.check_check_passed(check_passed=check_passed)
        if not regions_synced:
            raise ValueError("wait for regions to be synced")

        # Connect to both databases
        general_db = SQLAlchemyDatabase.from_kedro(credentials_name="postgres_general_data")
        company_db = SQLAlchemyDatabase.from_kedro(credentials_name="postgres")

        # Prepare company data as dictionary
        company_data = {
            "name": name,
            "dataset_type": dataset_type,
            "description": description,
            "min_date": min_date,
            "max_date": max_date,
            "frequency": frequency,
        }

        # First, write to general database
        from foundry_sdk.db_mgmt.tables_general_data import Companies as GeneralCompanies

        company_id = general_db.handle_insertion_single_line(
            model_class=GeneralCompanies,
            data=company_data,
            mode=self.insertion_mode,
            returning_id=True,
        )

        # Then write to company database with company_id
        from foundry_sdk.db_mgmt.tables_ts import Companies as TSCompanies

        company_data_with_id = company_data.copy()
        company_data_with_id["company_id"] = company_id

        try:
            company_db.handle_insertion_single_line(
                model_class=TSCompanies,
                data=company_data_with_id,
                mode=self.insertion_mode,
                returning_id=False,
            )
        except Exception:
            # Roll back general database write if company database write fails
            with general_db.get_session() as session:
                session.query(GeneralCompanies).filter(GeneralCompanies.company_id == company_id).delete()
                session.commit()
            raise

        logger.info("Writing company '%s' to both databases complete, got ID %s", name, company_id)
        return company_id

    def write_stores(self, store_region_map: pl.DataFrame, company_id: int, *, check_passed: bool) -> pl.DataFrame:
        """Write store entries to the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        db = SQLAlchemyDatabase.from_kedro()

        # Get unique combinations of region, country, level to look up region IDs
        region_lookup = store_region_map.select(["region", "country", "level"]).unique()

        with db.get_session(read_only=True) as session:
            # Query region IDs from database
            country_abbrevs = region_lookup.select("country").unique().to_series().to_list()
            country_query = (
                session.query(Regions.region_id, Regions.abbreviation)
                .filter(Regions.abbreviation.in_(country_abbrevs), Regions.type == "country")
                .all()
            )

            country_id_map = {abbrev: region_id for region_id, abbrev in country_query}

            # Build region lookup with country IDs
            region_lookup_with_country_ids = region_lookup.with_columns(
                pl.col("country").replace(country_id_map).alias("country_id").cast(pl.Int64)
            )

            # Query all region IDs in one batch
            region_conditions = [
                (Regions.abbreviation == row["region"])
                & (Regions.type == row["level"])
                & (Regions.country == row["country_id"])
                for row in region_lookup_with_country_ids.to_dicts()
            ]

            region_results = (
                session.query(Regions.region_id, Regions.abbreviation, Regions.type, Regions.country)
                .filter(or_(*region_conditions))
                .all()
            )

            # Build Polars DataFrame directly from results
            region_id_df = pl.DataFrame(
                [
                    {
                        "region_id": region_id,
                        "region": abbreviation,
                        "level": region_type,
                        "country_id": country_id,
                    }
                    for region_id, abbreviation, region_type, country_id in region_results
                ]
            )

        store_region_map = (
            store_region_map.join(region_lookup_with_country_ids, on=["region", "country", "level"], how="left")
            .join(region_id_df, on=["region", "country_id", "level"], how="left")
            .select(["store", "region_id"])
            .rename({"store": "name"})
            .with_columns(company_id=pl.lit(company_id))
        )

        # Use bulk insertion method
        result = db.handle_insertion_multi_line(
            model_class=Stores,
            data=store_region_map,
            mode=self.insertion_mode,
            returning_id=True,
        )

        logger.info("Writing stores to db complete, got %d store IDs back", len(result))

        return result

    def write_categories(
        self,
        categories_dict: dict,
        categories_level_description: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
    ) -> pl.DataFrame:
        """Writes categories and their relations to the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        db = SQLAlchemyDatabase.from_kedro()

        # Prepare category level descriptions
        categories_level_description = categories_level_description.with_columns(company_id=pl.lit(company_id)).sort(
            "level"
        )

        # Write category level descriptions
        db.handle_insertion_multi_line(
            model_class=CategoryLevelDescriptions,
            data=categories_level_description,
            mode=self.insertion_mode,
            returning_id=False,
        )
        logger.info("Successfully wrote %d category level descriptions", len(categories_level_description))

        all_categories = []
        all_relations = []

        # Process categories by level
        for row in categories_level_description.to_dicts():
            level = row["level"]
            level_name = row["name"]
            logger.info("Processing level %d: %s", level, level_name)

            relevant_categories = categories_dict[level]

            # Prepare unique categories for this level
            unique_categories = pl.DataFrame(
                {"name": list(relevant_categories.keys()), "company_id": [company_id] * len(relevant_categories)}
            )

            # Write categories for this level
            categories_result = db.handle_insertion_multi_line(
                model_class=Categories,
                data=unique_categories,
                mode=self.insertion_mode,
                returning_id=True,
            )

            all_categories.append(categories_result)

            # Process category relations if there are parent-child relationships
            if relevant_categories:
                relations_data = self._extract_category_relations(relevant_categories)
                if not relations_data.is_empty():
                    # Get category IDs for relations
                    relations_with_ids = self._resolve_category_relation_ids(
                        db, relations_data, company_id, is_top_level=level == categories_level_description[0, "level"]
                    )

                    if not relations_with_ids.is_empty():
                        # Write category relations
                        db.handle_insertion_multi_line(
                            model_class=CategoryRelations,
                            data=relations_with_ids,
                            mode=self.insertion_mode,
                            returning_id=False,
                        )
                        all_relations.append(relations_with_ids)

            logger.info("Successfully wrote level %d categories (%s) into the database", level, level_name)

        # Combine all category results
        if all_categories:
            return pl.concat(all_categories)

        return pl.DataFrame(schema={"name": pl.Utf8, "company_id": pl.Int64, "category_id": pl.Int64})

    def _extract_category_relations(self, categories_dict: dict) -> pl.DataFrame:
        """Extract parent-child relationships from categories dictionary."""
        relations = []

        for child_name, parents in categories_dict.items():
            if isinstance(parents, list | tuple | dict):
                parent_names = parents if isinstance(parents, list | tuple) else list(parents.keys())
                for parent_name in parent_names:
                    relations.append({"parentCategory": parent_name, "subCategory": child_name})

        if relations:
            return pl.DataFrame(relations)

        return pl.DataFrame(schema={"parentCategory": pl.Utf8, "subCategory": pl.Utf8})

    def _resolve_category_relation_ids(
        self,
        db: SQLAlchemyDatabase,
        relations_df: pl.DataFrame,
        company_id: int,
        *,
        is_top_level: bool,
    ) -> pl.DataFrame:
        """Resolve category names to IDs for relations."""
        if relations_df.is_empty():
            return pl.DataFrame(
                schema={"sub_category_id": pl.Int64, "parent_category_id": pl.Int64, "company_id": pl.Int64}
            )

        # Get unique category names
        sub_categories = relations_df.select("subCategory").unique().to_series().to_list()
        parent_categories = relations_df.select("parentCategory").unique().to_series().to_list()
        all_category_names = list(set(sub_categories + parent_categories))

        # Query category IDs in batch
        with db.get_session(read_only=True) as session:
            category_results = (
                session.query(Categories.category_id, Categories.name)
                .filter(Categories.company_id == company_id, Categories.name.in_(all_category_names))
                .all()
            )

        # Build category name to ID mapping
        category_id_map = {name: cat_id for cat_id, name in category_results}

        # Add IDs to relations
        relations_with_ids = relations_df.with_columns(
            [
                pl.col("subCategory").replace(category_id_map).alias("sub_category_id").cast(pl.Int64),
                pl.col("parentCategory").replace(category_id_map).alias("parent_category_id").cast(pl.Int64),
                pl.lit(company_id).alias("company_id"),
            ]
        ).select(["company_id", "sub_category_id", "parent_category_id"])

        # For top level, remove relations where parent ID is null (no parent)
        if is_top_level:
            relations_with_ids = relations_with_ids.drop_nulls()

        return relations_with_ids

    def write_products(self, products: pl.DataFrame, company_id: int, *, check_passed: bool) -> pl.DataFrame:
        """Writes product entries to the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        db = SQLAlchemyDatabase.from_kedro()

        products = (
            products.with_columns(
                company_id=pl.lit(company_id),
            )
            .drop("category")
            .rename({"product": "name"})
            .unique()
        )

        # Use bulk insertion method
        result = db.handle_insertion_multi_line(
            model_class=Products,
            data=products,
            mode=self.insertion_mode,
            returning_id=True,
        )

        logger.info("Writing products to db complete, got %d product IDs back", len(result))

        return result

    def write_product_categories(
        self,
        products: pl.DataFrame,
        product_ids: pl.DataFrame,
        category_ids: pl.DataFrame,
        *,
        check_passed: bool,
    ) -> pl.DataFrame:
        """Link products to categories and write associations."""
        DataLoader.check_check_passed(check_passed=check_passed)

        db = SQLAlchemyDatabase.from_kedro()

        products = (
            products.join(
                product_ids.rename({"name": "product", "product_id": "product_id"}),
                on=["product"],
                how="left",
            )
            .join(
                category_ids.select(["name", "category_id", "company_id"]).rename({"name": "category"}),
                on=["category"],
                how="left",
            )
            .select(["company_id", "product_id", "category_id"])
        )

        # Use bulk insertion method
        db.handle_insertion_multi_line(
            model_class=ProductCategories,
            data=products,
            mode=self.insertion_mode,
            returning_id=False,
        )

        logger.info("Writing product categories to db complete, linked %d product-category pairs", len(products))

        return True

    def write_skus(
        self,
        sales_data_map: pl.DataFrame,
        store_ids: pl.DataFrame,
        product_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
    ) -> pl.DataFrame:
        """Write SKU entries (product-store combinations) to the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        db = SQLAlchemyDatabase.from_kedro()

        # Get unique store-product pairs
        sales_data_map = (
            sales_data_map.select(["store", "product"])
            .unique()
            .with_columns(company_id=pl.lit(company_id))
            .join(store_ids.rename({"name": "store"}), on=["store", "company_id"], how="left")
            .join(product_ids.rename({"name": "product"}), on=["product", "company_id"], how="left")
        )
        skus = sales_data_map.select(["store_id", "product_id", "company_id"])

        # Write to SKU table
        result = db.handle_insertion_multi_line(
            model_class=SkuTable,
            data=skus,
            mode=self.insertion_mode,
            returning_id=True,
        )

        sales_data_map = sales_data_map.join(result, on=["store_id", "product_id", "company_id"], how="left")

        logger.info("Writing SKUs to db complete, got %d sku IDs back", len(result))

        return sales_data_map  # this is sku_ids in the next function

    def write_time_sku_data(
        self,
        time_sku_feature_description_map: pl.DataFrame,
        time_sku_data: pl.DataFrame,
        sku_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        strategy: TimeDataStrategy | str,
        num_workers: int = 1,
    ) -> bool:
        """
        Write Time-SKU-data into the database.

        Args:
            time_sku_feature_description_map: Feature descriptions for time-SKU features
            time_sku_data: Time-series SKU data
            sku_ids: SKU ID mappings
            company_id: Company identifier
            check_passed: Validation check flag
            strategy: Selected write approach for the time-series data
            num_workers: Number of parallel workers for processing

        """
        DataLoader.check_check_passed(check_passed=check_passed)

        feature_type = "time_sku"
        merge_col_names = ["product", "store"]
        select_col_names = ["feature_id", "company_id", "sku_id", "date", "value"]
        sql_table_class = TimeSkuFeatures
        sql_table_class_text = TimeSkuFeaturesText

        return self._write_time_feature_data(
            feature_description_map=time_sku_feature_description_map,
            time_data=time_sku_data,
            ids=sku_ids.select(["company_id", "product", "store", "sku_id"]),
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            strategy=strategy,
            num_workers=num_workers,
        )

    def write_flags(
        self,
        flags: pl.DataFrame,
        sku_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        strategy: TimeDataStrategy | str,
        num_workers: int = 1,
    ) -> bool:
        """
        Write flags to the database.

        Args:
            flags: Flag data to write
            sku_ids: SKU ID mappings
            company_id: Company identifier
            check_passed: Validation check flag
            strategy: Selected write approach for the time-series data
            num_workers: Number of parallel workers for processing

        """
        DataLoader.check_check_passed(check_passed=check_passed)

        if flags.is_empty():
            logger.info("No flags to write")
            return True

        db = SQLAlchemyDatabase.from_kedro()

        all_flags = [f.value for f in FlagLevels]

        flag_description_map = pl.DataFrame(
            {
                "name": all_flags,
                "description": ["Flag indicating ..."] * len(all_flags),
                "var_type": ["binary"] * len(all_flags),
                "company_id": [company_id] * len(all_flags),
                "feature_type": ["time_sku"] * len(all_flags),
            }
        )

        feature_description_result = db.handle_insertion_multi_line(
            model_class=FeatureDescriptions,
            data=flag_description_map,
            mode=self.insertion_mode,
            returning_id=True,
            parallel_workers=num_workers,
        )

        # Prepare flags for the new Flags table structure
        flags = (
            flags.with_columns(
                value=pl.lit(True).cast(pl.Boolean),  # Boolean flags for new schema
            )
            .rename({"flag": "feature"})
            .join(
                feature_description_result.rename({"name": "feature"}),
                on="feature",
                how="left",
            )
            .join(
                sku_ids.select(["company_id", "product", "store", "sku_id"]),
                on=["product", "store"],
                how="left",
            )
            .rename({"date": "ts"})
            .select(["company_id", "sku_id", "feature_id", "ts", "value"])
        )

        # Write flags using the same pattern as write_time_sku_data
        write_time_features(
            db,
            flags,
            model_cls=Flags,
            insertion_mode=self.insertion_mode,
            max_workers=num_workers,
            strategy=strategy,
        )

        logger.info("Writing flags to the database complete, wrote %d rows", len(flags))

        return True

    def write_sales(
        self,
        sales: pl.DataFrame,
        sku_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        strategy: TimeDataStrategy | str,
        num_workers: int = 4,
    ) -> bool:
        """
        Write sales data to OrderIntake, ExpectedDeliveries, and ChangeLogCommitted tables.

        Args:
            sales: DataFrame with columns (store, product, order_date, delivery_date, quantity)
            sku_ids: DataFrame with SKU ID mappings
            company_id: Company identifier
            check_passed: Validation check flag
            strategy: Selected write approach for time data (append, update, or ignore)
            num_workers: Number of parallel workers for processing
            time_window_days: Optional time window in days for incremental processing.
                            If provided, only processes records within this many days from today.
                            Helps with TimescaleDB chunk pruning for better performance.

        """
        DataLoader.check_check_passed(check_passed=check_passed)

        if sales.is_empty():
            logger.info("No sales data to write")
            return True
        
        effective_strategy = get_time_data_strategy(strategy)
        if effective_strategy is TimeDataStrategy.IGNORE:
            logger.info("Sales strategy IGNORE — skipping order intake and downstream writes.")
            return True
        
        logger.info("Processing %d sales records", len(sales))
        db = SQLAlchemyDatabase.from_kedro()

        # Step 1: Transform sales data to OrderIntake format
        # Expected sales columns: store, product, order_date, delivery_date, quantity (float64)

        # Join with sku_ids to get company_id and sku_id mapping
        sales = (
            sales.join(
                sku_ids.select(["company_id", "product", "store", "sku_id"]),
                on=["product", "store"],
                how="left",
            )
            .drop(["store", "product"])
        )

        # Verify company_id consistency
        if not sales.filter(pl.col("company_id") != company_id).is_empty():
            logger.warning("Mismatched company_id in sales data")


        # Step 2: Write aggregated data to OrderIntake table using write_time_features
        write_time_features(
            db,
            sales,
            model_cls=OrderIntake,
            insertion_mode=self.insertion_mode,
            max_workers=num_workers,
            strategy=effective_strategy,
        )

        logger.info("Writing OrderIntake data complete, wrote %d rows", len(sales))

        # deliveries_table = ExpectedDeliveries.__table__
        # deliveries_schema = deliveries_table.schema or "public"

        # with db.engine.begin() as conn:
        #     deliveries_empty = _is_table_empty(conn, deliveries_schema, deliveries_table.name)

        # if deliveries_empty:
            # logger.info(
            #     "ExpectedDeliveries is empty — aggregating incoming sales for initial build (company %s).",
            #     company_id,
            # )
        deliveries_df = (
            sales.select(["company_id", "sku_id", "expected_delivery_date", "quantity"])
            .group_by(["company_id", "sku_id", "expected_delivery_date"], maintain_order=False)
            .agg(pl.col("quantity").sum().alias("quantity"))
            .sort(["expected_delivery_date", "sku_id"], maintain_order=False)
        )

        if deliveries_df.is_empty():
            logger.info(
                "No aggregated deliveries rows computed for company %s; skipping initial ExpectedDeliveries load.",
                company_id,
            )
        else:
            write_time_features(
                db,
                deliveries_df,
                model_cls=ExpectedDeliveries,
                insertion_mode=self.insertion_mode,
                max_workers=num_workers,
                strategy=TimeDataStrategy.APPEND,
            )
            total_qty = deliveries_df.select(pl.col("quantity").sum()).item()
            logger.info(
                "ExpectedDeliveries initial build finished for company %s (%d rows, total qty %.4f).",
                company_id,
                deliveries_df.height,
                total_qty,
            )

        # change_log_table = ChangeLogCommitted.__table__
        # change_log_schema = change_log_table.schema or "public"

        # with db.engine.begin() as conn:
        #     change_log_empty = _is_table_empty(conn, change_log_schema, change_log_table.name)

        # if change_log_empty:
            # logger.info(
            #     "ChangeLogCommitted is empty — building initial change log for company %s.",
            #     company_id,
            # )

        change_log_df = (
            sales.select(
                [
                    "company_id",
                    "sku_id",
                    "expected_delivery_date",
                    "order_date",
                    "quantity",
                ]
            )
            .group_by(
                ["company_id", "sku_id", "expected_delivery_date", "order_date"],
                maintain_order=False,
            )
            .agg(pl.col("quantity").sum().alias("delta_quantity"))
            .sort(
                ["company_id", "sku_id", "expected_delivery_date", "order_date"],
                maintain_order=False,
            )
            .with_columns(
                pl.col("delta_quantity")
                .cum_sum()
                .over(["company_id", "sku_id", "expected_delivery_date"])
                .alias("quantity")
            )
            .rename({"order_date": "valid_from"})
            .select(["company_id", "sku_id", "expected_delivery_date", "valid_from", "quantity"])
        )

        if change_log_df.is_empty():
            logger.info(
                "No change-log rows computed for company %s; skipping initial ChangeLogCommitted load.",
                company_id,
            )
        else:
            write_time_features(
                db,
                change_log_df,
                model_cls=ChangeLogCommitted,
                insertion_mode=self.insertion_mode,
                max_workers=num_workers,
                strategy=TimeDataStrategy.APPEND,
            )

            final_committed = (
                change_log_df.select(pl.col("quantity").max()).item()
                if change_log_df.height > 0
                else 0
            )
            logger.info(
                "ChangeLogCommitted initial build finished for company %s (%d rows, final committed qty %.4f).",
                company_id,
                change_log_df.height,
                final_committed,
            )


        return True

    # #################################### Optional data #############################################

    def _write_levels(
        self,
        db: SQLAlchemyDatabase,
        feature_description_map: pl.DataFrame,
        feature_description_result: pl.DataFrame,
    ) -> None:
        num_cat = feature_description_map.filter(pl.col("var_type") == "categorical").shape[0]

        if num_cat == 0:
            return

        feature_description_map = (
            feature_description_map.filter(pl.col("var_type") == "categorical")
            .join(
                feature_description_result.select(["name", "feature_id"]),
                on="name",
                how="left",
            )
            .drop(["description", "name", "var_type", "company_id"])
            .explode("levels")
            .with_row_index("order")
            .rename({"levels": "level"})
            .select(["feature_id", "level", pl.col("order").cast(pl.Int32)])
        )

        db.handle_insertion_multi_line(
            model_class=FeatureLevels,
            data=feature_description_map,
            mode=self.insertion_mode,
            returning_id=False,
        )

    def _write_non_time_feature_data(
        self,
        feature_description_map: pl.DataFrame,
        feature_map: pl.DataFrame,
        ids: pl.DataFrame,
        company_id: int,
        feature_type: str,
        merge_col_names: list[str],
        select_col_names: list[str],
        sql_table_class: DeclarativeMeta,
        sql_table_class_text: DeclarativeMeta,
        num_workers: int = 1,
    ) -> bool:
        db = SQLAlchemyDatabase.from_kedro()

        if feature_description_map.is_empty():
            logger.info("No feature data to write for %s features", feature_type)
            return True

        # Prepare feature description map
        feature_description_map_for_insert = feature_description_map.with_columns(
            company_id=pl.lit(company_id), feature_type=pl.lit(feature_type)
        ).drop("levels")

        # Write feature descriptions
        feature_description_result = db.handle_insertion_multi_line(
            model_class=FeatureDescriptions,
            data=feature_description_map_for_insert,
            mode=self.insertion_mode,
            returning_id=True,
        )

        self._write_levels(db, feature_description_map, feature_description_result)

        # Join feature_map with feature descriptions to get feature_id
        feature_map = feature_map.join(
            feature_description_result.select(["name", "feature_id"]).rename({"name": "feature"}),
            on="feature",
            how="left",
        ).join(
            ids,
            on=merge_col_names,
            how="left",
        )

        feature_map = feature_map.select(select_col_names)

        # Join with feature descriptions to get var_type for separation
        feature_description_result = feature_description_result.join(
            feature_description_map.select(["name", "var_type"]),
            on="name",
            how="left",
        )

        # Separate numeric and text features based on var_type
        numeric_data = feature_map.join(
            feature_description_result.filter(pl.col("var_type").is_in(NUMERIC_VAR_TYPES)).select("feature_id"),
            on="feature_id",
            how="inner",
        )

        text_data = feature_map.join(
            feature_description_result.filter(pl.col("var_type").is_in(TEXT_VAR_TYPES)).select("feature_id"),
            on="feature_id",
            how="inner",
        )

        # Write numeric features
        if numeric_data.height > 0:
            db.handle_insertion_multi_line(
                model_class=sql_table_class,
                data=numeric_data,
                mode=self.insertion_mode,
                returning_id=False,
                parallel_workers=num_workers,
            )
            logger.info("Writing %s numeric features to the database complete, wrote %d rows", feature_type, len(numeric_data))

        # Write text features
        if text_data.height > 0:
            db.handle_insertion_multi_line(
                model_class=sql_table_class_text,
                data=text_data,
                mode=self.insertion_mode,
                returning_id=False,
                parallel_workers=num_workers,
            )
            logger.info("Writing %s text features to the database complete, wrote %d rows", feature_type, len(text_data))

        return True

    def _write_time_feature_data(
        self,
        feature_description_map: pl.DataFrame,
        time_data: pl.DataFrame,
        ids: pl.DataFrame,
        company_id: int,
        feature_type: str,
        merge_col_names: list[str],
        select_col_names: list[str],
        sql_table_class: DeclarativeMeta,
        sql_table_class_text: DeclarativeMeta,
        *,
        strategy: TimeDataStrategy | str,
        num_workers: int = 1,
    ) -> bool:
        """
        Helper function for writing time-based feature data.
        
        Handles the common pattern of:
        1. Writing feature descriptions
        2. Writing categorical levels
        3. Joining time data with features and IDs
        4. Separating numeric vs text features
        5. Writing to TimescaleDB tables using write_time_features
        """
        db = SQLAlchemyDatabase.from_kedro()

        if feature_description_map.is_empty():
            logger.info("No feature data to write for %s features", feature_type)
            return True

        # Prepare feature description map
        feature_description_map_for_insert = feature_description_map.with_columns(
            company_id=pl.lit(company_id), feature_type=pl.lit(feature_type)
        ).drop("levels")

        # Write feature descriptions
        feature_description_result = db.handle_insertion_multi_line(
            model_class=FeatureDescriptions,
            data=feature_description_map_for_insert,
            mode=self.insertion_mode,
            returning_id=True,
        )

        # Write categorical levels
        self._write_levels(db, feature_description_map, feature_description_result)

        # Join time data with feature descriptions and IDs
        time_data = (
            time_data.join(
                feature_description_result.rename({"name": "feature"}),
                on="feature",
                how="left",
            )
            .join(
                ids,
                on=merge_col_names,
                how="left",
            )
            .select(select_col_names)
        )

        # Get var_type info for separation
        feature_description_result = feature_description_result.join(
            feature_description_map.select(["name", "var_type"]),
            on="name",
            how="left",
        )

        # Separate numeric and text features based on var_type
        numeric_data = time_data.join(
            feature_description_result.filter(pl.col("var_type").is_in(NUMERIC_VAR_TYPES)).select("feature_id"),
            on="feature_id",
            how="inner",
        )

        text_data = time_data.join(
            feature_description_result.filter(pl.col("var_type").is_in(TEXT_VAR_TYPES)).select("feature_id"),
            on="feature_id",
            how="inner",
        )

        # Rename date to ts for TimescaleDB
        numeric_data = numeric_data.rename({"date": "ts"})
        text_data = text_data.rename({"date": "ts"})

        # Write numeric features using TimescaleDB approach
        write_time_features(
            db,
            numeric_data,
            model_cls=sql_table_class,
            insertion_mode=self.insertion_mode,
            max_workers=num_workers,
            strategy=strategy,
        )

        # Write text features using TimescaleDB approach
        if text_data.height > 0:
            write_time_features(
                db,
                text_data,
                model_cls=sql_table_class_text,
                insertion_mode=self.insertion_mode,
                max_workers=num_workers,
                strategy=strategy,
            )

        return True

    def write_store_data(
        self,
        store_feature_description_map: pl.DataFrame,
        store_feature_map: pl.DataFrame,
        store_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        num_workers: int = 1,
    ) -> bool:
        """Write store data into the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        feature_type = "store"
        merge_col_names = ["store"]
        select_col_names = ["company_id", "store_id", "feature_id", "value"]
        sql_table_class = StoreFeatures
        sql_table_class_text = StoreFeaturesText

        return self._write_non_time_feature_data(
            feature_description_map=store_feature_description_map,
            feature_map=store_feature_map,
            ids=store_ids.rename({"name": "store"}),
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            num_workers=num_workers,
        )

    def write_product_data(
        self,
        product_feature_description_map: pl.DataFrame,
        product_feature_map: pl.DataFrame,
        product_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        num_workers: int = 1,
    ) -> bool:
        """Write product data into the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        feature_type = "product"
        merge_col_names = ["product"]
        select_col_names = ["company_id", "product_id", "feature_id", "value"]
        sql_table_class = ProductFeatures
        sql_table_class_text = ProductFeaturesText

        return self._write_non_time_feature_data(
            feature_description_map=product_feature_description_map,
            feature_map=product_feature_map,
            ids=product_ids.rename({"name": "product"}),
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            num_workers=num_workers,
        )

    def write_sku_data(
        self,
        sku_feature_description_map: pl.DataFrame,
        sku_feature_map: pl.DataFrame,
        sku_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        num_workers: int = 1,
    ) -> bool:
        """Write SKU data into the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        feature_type = "sku"
        merge_col_names = ["product", "store"]
        select_col_names = ["company_id", "sku_id", "feature_id", "value"]
        sql_table_class = SkuFeatures
        sql_table_class_text = SkuFeaturesText

        return self._write_non_time_feature_data(
            feature_description_map=sku_feature_description_map,
            feature_map=sku_feature_map,
            ids=sku_ids,
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            num_workers=num_workers,
        )

    def write_time_product_data(
        self,
        time_product_feature_description_map: pl.DataFrame,
        time_product_feature_map: pl.DataFrame,
        product_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        strategy: TimeDataStrategy | str,
        num_workers: int = 1,
    ) -> bool:
        """Write time-product data into the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        feature_type = "time_product"
        merge_col_names = ["product"]
        select_col_names = ["feature_id", "company_id", "product_id", "date", "value"]
        sql_table_class = TimeProductFeatures
        sql_table_class_text = TimeProductFeaturesText

        return self._write_time_feature_data(
            feature_description_map=time_product_feature_description_map,
            time_data=time_product_feature_map,
            ids=product_ids.rename({"name": "product"}),
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            strategy=strategy,
            num_workers=num_workers,
        )

    def write_time_store_data(
        self,
        time_store_feature_description_map: pl.DataFrame,
        time_store_feature_map: pl.DataFrame,
        store_ids: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        strategy: TimeDataStrategy | str,
        num_workers: int = 1,
    ) -> bool:
        """Write time-store data into the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        feature_type = "time_store"
        merge_col_names = ["store"]
        select_col_names = ["feature_id", "company_id", "store_id", "date", "value"]
        sql_table_class = TimeStoreFeatures
        sql_table_class_text = TimeStoreFeaturesText

        return self._write_time_feature_data(
            feature_description_map=time_store_feature_description_map,
            time_data=time_store_feature_map,
            ids=store_ids.rename({"name": "store"}),
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            strategy=strategy,
            num_workers=num_workers,
        )

    def write_time_region_data(
        self,
        time_region_feature_description_map: pl.DataFrame,
        time_region_feature_map: pl.DataFrame,
        company_id: int,
        *,
        check_passed: bool,
        strategy: TimeDataStrategy | str,
        num_workers: int = 1,
    ) -> bool:
        """Write time-region data into the database."""
        DataLoader.check_check_passed(check_passed=check_passed)

        if time_region_feature_description_map.is_empty():
            logger.info("No time-region feature data to write")
            return True

        db = SQLAlchemyDatabase.from_kedro()

        # Get unique combinations of region, country, level to look up region IDs
        region_lookup = time_region_feature_map.select(["region", "country", "level"]).unique()
        time_region_feature_map = time_region_feature_map.with_columns(company_id=pl.lit(company_id))

        with db.get_session(read_only=True) as session:
            # Query region IDs from database
            country_abbrevs = region_lookup.select("country").unique().to_series().to_list()
            country_query = (
                session.query(Regions.region_id, Regions.abbreviation)
                .filter(Regions.abbreviation.in_(country_abbrevs), Regions.type == "country")
                .all()
            )

            country_id_map = {abbrev: region_id for region_id, abbrev in country_query}

            # Build region lookup with country IDs
            region_lookup_with_country_ids = region_lookup.with_columns(
                pl.col("country").replace(country_id_map).alias("country_id").cast(pl.Int64)
            )

            # Query all region IDs in one batch
            region_conditions = [
                (Regions.abbreviation == row["region"])
                & (Regions.type == row["level"])
                & (Regions.country == row["country_id"])
                for row in region_lookup_with_country_ids.to_dicts()
            ]

            region_results = (
                session.query(Regions.region_id, Regions.abbreviation, Regions.type, Regions.country)
                .filter(or_(*region_conditions))
                .all()
            )

            # Build Polars DataFrame for region IDs
            region_ids = pl.DataFrame(
                [
                    {
                        "region_id": region_id,
                        "region": abbreviation,
                        "level": region_type,
                        "country_id": country_id,
                    }
                    for region_id, abbreviation, region_type, country_id in region_results
                ]
            )

        # Join with country lookup to get country names back
        region_ids = region_ids.join(
            region_lookup_with_country_ids, on=["region", "country_id", "level"], how="left"
        ).select(["region_id", "region", "country", "level"])

        feature_type = "time_region"
        merge_col_names = ["region", "country", "level"]  # Match on region, country, level
        select_col_names = ["date", "company_id", "region_id", "feature_id", "value"]  # Include date_id for time features
        sql_table_class = TimeRegionFeatures
        sql_table_class_text = TimeRegionFeaturesText

        return self._write_time_feature_data(
            feature_description_map=time_region_feature_description_map,
            time_data=time_region_feature_map,
            ids=region_ids,
            company_id=company_id,
            feature_type=feature_type,
            merge_col_names=merge_col_names,
            select_col_names=select_col_names,
            sql_table_class=sql_table_class,
            sql_table_class_text=sql_table_class_text,
            strategy=strategy,
            num_workers=num_workers,
        )


####################################################################################################
#################################### Temporary, to be moved to separate file #######################
####################################################################################################

import logging
import polars as pl

logger = logging.getLogger(__name__)


def _build_insert_sql(
    target_table: str,
    staging_table: str,
    *,
    cols: list[str],
    unique_keys: list[str],
    insertion_mode: str,
) -> str:
    """Generate PostgreSQL UPSERT SQL with conflict resolution.

    Supports three modes: RAISE (fail on conflict), IGNORE (skip conflicts),
    UPDATE (update non-unique columns with change detection guard).
    """
    insert_cols = ", ".join(cols)
    select_cols = ", ".join(cols)
    prefix = f"INSERT INTO {target_table} AS t ({insert_cols})\nSELECT {select_cols}\nFROM {staging_table}"

    mode = insertion_mode.upper()
    if mode == "RAISE":
        return prefix

    pk = ", ".join(unique_keys)

    if mode == "IGNORE":
        return f"""{prefix}
ON CONFLICT ({pk}) DO NOTHING
"""

    # default: UPDATE — update all non-unique columns, guarded to skip no-op updates
    non_unique = [c for c in cols if c not in unique_keys]
    if not non_unique:
        return f"""{prefix}
ON CONFLICT ({pk}) DO NOTHING
"""
    set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in non_unique])
    guard = " OR ".join([f"(t.{c} IS DISTINCT FROM EXCLUDED.{c})" for c in non_unique])
    return f"""{prefix}
ON CONFLICT ({pk})
DO UPDATE SET {set_clause}
WHERE {guard}
"""


def _validate_columns_or_die(df: pl.DataFrame, table_columns: list[str]) -> None:
    """Validate DataFrame columns against target table schema, raise on mismatch."""
    missing = [c for c in df.columns if c not in table_columns]
    if missing:
        raise ValueError(
            f"DataFrame has columns not present in target table: {missing}. Allowed columns: {table_columns}"
        )


def _get_table_metadata(model_cls):
    """Extract (schema, table_name, time_column, space_column, unique_keys, table_columns, compress_after)."""
    table = model_cls.__table__
    schema = table.schema or "public"
    table_name = table.name
    table_columns = [c.name for c in table.columns]

    ts_info = getattr(table, "info", {}).get("timescale", {})
    time_column = ts_info.get("time_column")
    space_column = ts_info.get("space_column")
    compress_after = (ts_info.get("compression") or {}).get("compress_after")

    unique_keys = getattr(model_cls, "__unique_keys__", None) or [c.name for c in table.primary_key.columns]
    return schema, table_name, time_column, space_column, unique_keys, table_columns, compress_after


def _pause_compression(conn, fq_table: str, new_after: str = "100 years") -> None:
    """Pause compression policy during bulk operations to avoid conflicts with chunk writes."""
    try:
        conn.execute(text(f"SELECT alter_compression_policy('{fq_table}', INTERVAL '{new_after}');"))
    except Exception as e:
        logger.debug("alter_compression_policy not available or failed for %s: %s", fq_table, e)


def _resume_compression(conn, fq_table: str, original_after: str | None) -> None:
    """Restore original compression policy after bulk operations complete."""
    if not original_after:
        return
    try:
        conn.execute(text(f"SELECT alter_compression_policy('{fq_table}', INTERVAL '{original_after}');"))
    except Exception as e:
        logger.debug("alter_compression_policy restore failed for %s: %s", fq_table, e)


def _decompress_overlapping_chunks(conn, table_name: str, min_date, max_date) -> None:
    """Decompress TimescaleDB chunks that overlap with incoming data time range.

    Only decompresses compressed chunks to enable efficient upsert operations.
    """
    try:
        q = text(
            """
            SELECT format('%I.%I', chunk_schema, chunk_name) AS fqname
            FROM timescaledb_information.chunks
            WHERE hypertable_name = :ht
              AND range_start <= (:maxd)::timestamp
              AND range_end   >= (:mind)::timestamp
              AND is_compressed
            """
        )
        rows = conn.execute(q, {"ht": table_name, "mind": str(min_date), "maxd": str(max_date)}).fetchall()
        for (fqname,) in rows:
            try:
                conn.execute(text(f"SELECT decompress_chunk('{fqname}');"))
                logger.info("Decompressed chunk %s for %s", fqname, table_name)
            except Exception as e:
                logger.debug("decompress_chunk failed for %s: %s", fqname, e)
    except Exception as e:
        logger.debug("Could not enumerate chunks for %s: %s", table_name, e)


def _is_table_empty(conn, schema: str, table: str) -> bool:
    """Check if table contains any data to determine optimal write strategy."""
    res = conn.execute(text(f'SELECT 1 FROM "{schema}"."{table}" LIMIT 1')).fetchone()
    return res is None


# =========================
# Workers (module scope for pickling)
# =========================
def _copy_upsert_month_worker(
    month_key: str,
    csv_txt: str,
    row_count: int,
    *,
    cols: list[str],
    unique_keys: list[str],
    target_table: str,  # fully-qualified "schema.table"
    staging_prefix: str,
    insertion_mode: str,
    strategy: str,
) -> int:
    """Non-empty table worker: COPY → UPSERT (ON CONFLICT) → DROP staging; returns row_count."""
    from foundry_sdk.db_mgmt import SQLAlchemyDatabase

    db = SQLAlchemyDatabase.from_kedro()
    staging_table = f"{staging_prefix}_{month_key.replace('-', '_')}_{uuid4().hex[:8]}"

    create_staging_sql = f"CREATE UNLOGGED TABLE {staging_table} (LIKE {target_table});"
    copy_columns = ", ".join(cols)
    copy_sql = f"COPY {staging_table} ({copy_columns}) FROM STDIN WITH (FORMAT csv, HEADER true);"
    upsert_sql = _build_insert_sql(
        target_table=target_table,
        staging_table=staging_table,
        cols=cols,
        unique_keys=unique_keys,
        insertion_mode=insertion_mode,
    )

    speed_tweaks = ["SET LOCAL synchronous_commit = off", "SET LOCAL wal_compression = on"]

    strategy_enum = TimeDataStrategy(strategy)
    perform_dedup = strategy_enum is TimeDataStrategy.UPDATE

    with db.engine.begin() as conn:
        conn.execute(text(create_staging_sql))
        for stmt in speed_tweaks:
            conn.execute(text(stmt))
        raw = getattr(conn.connection, "connection", None) or getattr(conn.connection, "driver_connection", None)
        cur = raw.cursor()
        cur.copy_expert(copy_sql, StringIO(csv_txt))

    rows_to_upsert = row_count
    skipped_rows = 0

    with db.engine.begin() as conn:
        for stmt in speed_tweaks:
            conn.execute(text(stmt))
        if perform_dedup:
            skipped_rows = _delete_identical_rows(
                conn,
                staging_table,
                target_table,
                unique_keys=unique_keys,
                all_columns=cols,
            )
            rows_to_upsert = _table_rowcount(conn, staging_table)
            logger.info(
                "Month %s: found %d identical rows to skip, %d rows to upsert after deduplication",
                month_key,
                skipped_rows,
                rows_to_upsert,
            )

        if rows_to_upsert == 0:
            conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))
        else:
            conn.execute(text(upsert_sql))
            conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))

    db.engine.dispose()
    
    return row_count


def _copy_direct_batch_worker(
    *,
    schema: str,
    table: str,
    batch_key: str,
    payload: bytes | str,
    is_binary: bool,
    row_count: int,
    cols: list[str],
) -> int:
    """
    Empty-table worker: DIRECT COPY into the hypertable (no staging).
    If is_binary=True, uses COPY ... FORMAT binary. Else CSV.
    """
    from foundry_sdk.db_mgmt import SQLAlchemyDatabase

    db = SQLAlchemyDatabase.from_kedro()
    fq_target = f'"{schema}"."{table}"'
    copy_columns = ", ".join(cols)

    if is_binary:
        copy_sql = f"COPY {fq_target} ({copy_columns}) FROM STDIN WITH (FORMAT binary);"
    else:
        copy_sql = f"COPY {fq_target} ({copy_columns}) FROM STDIN WITH (FORMAT csv, HEADER true);"

    speed = ["SET LOCAL synchronous_commit = off", "SET LOCAL wal_compression = on"]

    with db.engine.begin() as conn:
        for s in speed:
            conn.execute(text(s))
        raw = getattr(conn.connection, "connection", None) or getattr(conn.connection, "driver_connection", None)

        # psycopg2 and psycopg3 both expose .cursor(); copy_expert works for both
        cur = raw.cursor()
        if isinstance(payload, str):
            buf = StringIO(payload)
        else:
            buf = BytesIO(payload)
        cur.copy_expert(copy_sql, buf)

    db.engine.dispose()
    return row_count




def _quote_ident(name: str) -> str:
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def _delete_identical_rows(
    conn,
    staging_table: str,
    target_table: str,
    *,
    unique_keys: list[str],
    all_columns: list[str],
) -> int:
    if not unique_keys:
        return 0

    key_conditions = [f"s.{_quote_ident(col)} = t.{_quote_ident(col)}" for col in unique_keys]
    non_key_columns = [col for col in all_columns if col not in unique_keys]

    condition = " AND ".join(key_conditions)
    if non_key_columns:
        comparisons = [f"s.{_quote_ident(col)} IS NOT DISTINCT FROM t.{_quote_ident(col)}" for col in non_key_columns]
        condition = f"{condition} AND " + " AND ".join(comparisons)

    delete_sql = text(
        f"""
        DELETE FROM {staging_table} AS s
        USING {target_table} AS t
        WHERE {condition}
        """
    )

    result = conn.execute(delete_sql)
    return result.rowcount or 0


def _table_rowcount(conn, table_name: str) -> int:
    res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    value = res.scalar()
    return int(value or 0)


# =========================
# Public API (no index drop/rebuild)
# =========================
def write_time_features(
    db,
    df: pl.DataFrame,
    *,
    model_cls,
    insertion_mode: str = "UPDATE",  # 'UPDATE' | 'IGNORE' | 'RAISE'
    max_workers: int = 1,  # 1 = serial, >1 = parallel
    staging_prefix: str | None = None,
    strategy: TimeDataStrategy | str,
):
    """Optimized bulk write operations for TimescaleDB hypertables.

    Implements dual-path strategy:
    - Empty tables: Direct COPY with quarterly batching for optimal chunk alignment
    - Non-empty tables: Staging table UPSERT with monthly batching and optional chunk comparison

    Strategy UPDATE enables intelligent chunk comparison to skip identical data chunks,
    avoiding unnecessary decompressions for update-heavy workloads.

    Args:
        insertion_mode: 'UPDATE' (default), 'IGNORE', or 'RAISE'
        max_workers: Parallel worker count (1 = serial)
        strategy: Explicit time-data strategy for this write operation
    """
    if df.height == 0:
        logger.warning("Received empty DataFrame, skipping writing to DB.")
        return

    (schema, table_name, time_column, space_column, unique_keys, table_columns, compress_after) = _get_table_metadata(
        model_cls
    )
    _validate_columns_or_die(df, table_columns)

    if time_column not in df.columns:
        raise ValueError(f"DataFrame is missing the declared time column '{time_column}' for table '{table_name}'.")

    fq_table = f'"{schema}"."{table_name}"'
    cols = list(df.columns)
    if not staging_prefix:
        staging_prefix = f"staging_{table_name}"

    # Global window
    min_date = df.select(pl.col(time_column).min()).item()
    max_date = df.select(pl.col(time_column).max()).item()

    effective_strategy = get_time_data_strategy(strategy)

    # Empty table detection
    with db.engine.begin() as conn:
        table_is_empty = _is_table_empty(conn, schema, table_name)

    # -------- EMPTY TABLE: direct COPY into hypertable, quarterly batching --------
    if table_is_empty:
        logger.warning("trying out new strategy")
        if effective_strategy is TimeDataStrategy.IGNORE:
            logger.info(
                "Skipping initial load for %s.%s because strategy is IGNORE.",
                schema,
                table_name,
            )
            return

        logger.info(
            "Initial load detected for %s.%s — DIRECT COPY into hypertable (strategy=%s).",
            schema,
            table_name,
            effective_strategy.value,
        )

        with db.engine.begin() as conn:
            _pause_compression(conn, f"{schema}.{table_name}", new_after="100 years")
            _decompress_overlapping_chunks(conn, table_name, min_date, max_date)

        # Decide on binary capability:
        # - If underlying driver is psycopg (v3), we'll try binary COPY.
        # - If psycopg2, fall back to CSV (we'd need to hand-pack the binary protocol otherwise).
        try:
            can_binary = True
        except Exception:
            can_binary = False
        if can_binary:
            logger.info("Binary COPY supported (psycopg v3). Using FORMAT binary for initial load.")
        else:
            logger.info("psycopg v3 not detected; falling back to CSV COPY for initial load.")

        # Prepare balanced payloads that span the whole time range while keeping each series together
        logger.info("Preparing balanced batches for direct COPY...")

        # Ensure deterministic pseudo-random shuffling of space groups
        shuffled_series: list[pl.DataFrame]
        if space_column and space_column in cols:
            grouped = df.sort([space_column, time_column]).partition_by(space_column, as_dict=True, maintain_order=True)
            group_items = list(grouped.items())
            random.Random(0).shuffle(group_items)
            shuffled_series = [part.sort(time_column) for _, part in group_items]
        else:
            shuffled_series = [df.sort(time_column)]

        batch_row_limit = 1_000_000
        copy_batches: list[tuple[str, bytes | str, bool, int]] = []
        current_parts: list[pl.DataFrame] = []
        current_rows = 0

        def flush_batch(batch_id: int, parts: list[pl.DataFrame]) -> None:
            if not parts:
                return
            batch_df = pl.concat(parts, how="vertical") if len(parts) > 1 else parts[0]
            buf = BytesIO()
            batch_df.write_csv(buf)
            payload = buf.getvalue().decode("utf-8")
            copy_batches.append((f"batch_{batch_id:05d}", payload, False, batch_df.height))

        batch_idx = 0
        for series_df in shuffled_series:
            rows = series_df.height
            # Always keep a series intact; start a new batch if it would exceed the row limit
            if current_rows and current_rows + rows > batch_row_limit:
                flush_batch(batch_idx, current_parts)
                batch_idx += 1
                current_parts = []
                current_rows = 0

            current_parts.append(series_df)
            current_rows += rows

        flush_batch(batch_idx, current_parts)

        logger.info("Prepared %d COPY batches for direct load (batch size ≈ %d rows).", len(copy_batches), batch_row_limit)
        total_rows = df.height
        with tqdm(
            total=total_rows, desc=f"Writing {table_name} (fast-load, direct)", unit="rows", dynamic_ncols=True
        ) as pbar:
            if max_workers > 1:
                with ProcessPoolExecutor(max_workers=max_workers) as ex:
                    futs = [
                        ex.submit(
                            _copy_direct_batch_worker,
                            schema=schema,
                            table=table_name,
                            batch_key=batch_id,
                            payload=payload,
                            is_binary=is_bin,
                            row_count=rows,
                            cols=cols,
                        )
                        for (batch_id, payload, is_bin, rows) in copy_batches
                    ]
                    for f in as_completed(futs):
                        pbar.update(f.result())
            else:
                for batch_id, payload, is_bin, rows in copy_batches:
                    processed = _copy_direct_batch_worker(
                        schema=schema,
                        table=table_name,
                        batch_key=batch_id,
                        payload=payload,
                        is_binary=is_bin,
                        row_count=rows,
                        cols=cols,
                    )
                    pbar.update(processed)

        logger.info("Resuming compression policy for %s.%s", schema, table_name)
        with db.engine.begin() as conn:
            conn.execute(text(f'ANALYZE "{schema}"."{table_name}"'))
            _resume_compression(conn, f"{schema}.{table_name}", compress_after)
        return

    if effective_strategy is TimeDataStrategy.IGNORE:
        logger.info("Strategy IGNORE selected for %s.%s; skipping write for non-empty table.", schema, table_name)
        return

    if effective_strategy is TimeDataStrategy.APPEND:
        append_allowed = _validate_append_mode(db, model_cls, df, time_column=time_column)
        if not append_allowed:
            logger.warning(
                "APPEND validation failed for %s.%s; falling back to UPDATE strategy.",
                schema,
                table_name,
            )
            effective_strategy = TimeDataStrategy.UPDATE
        else:
            logger.info(
                "APPEND validation passed for %s.%s; using fast append path.",
                schema,
                table_name,
            )

    if effective_strategy is TimeDataStrategy.UPDATE:
        logger.info(
            "UPDATE strategy for %s.%s; relying on TimescaleDB automatic chunk decompression.",
            schema,
            table_name,
        )

    # -------- NON-EMPTY TABLE: original UPSERT path (month batches + staging) --------
    # Month key batching for upsert
    mdf = df.with_columns(pl.col(time_column).dt.strftime("%Y-%m").alias("_month_key"))
    sort_cols = [c for c in (time_column, space_column) if c in cols]
    batches: list[tuple[str, str, int]] = []
    for _, subdf in mdf.group_by("_month_key", maintain_order=True):
        subdf = subdf.sort(sort_cols)
        buf = BytesIO()
        subdf.drop("_month_key").write_csv(buf)
        csv_txt = buf.getvalue().decode("utf-8")
        month_key = subdf.select(pl.col("_month_key")).unique().item()
        batches.append((month_key, csv_txt, subdf.height))

    total_rows = df.height
    batch_insertion_mode = ("RAISE" if effective_strategy is TimeDataStrategy.APPEND else insertion_mode)
    batch_insertion_mode = batch_insertion_mode.upper()

    with tqdm(total=total_rows, desc=f"Writing {table_name}", unit="rows", dynamic_ncols=True) as pbar:
        if max_workers > 1:
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futures = [
                    ex.submit(
                        _copy_upsert_month_worker,
                        month_key,
                        csv_txt,
                        row_count,
                        cols=cols,
                        unique_keys=unique_keys,
                        target_table=f'"{schema}"."{table_name}"',
                        staging_prefix=staging_prefix,
                        insertion_mode=batch_insertion_mode,
                        strategy=effective_strategy.value,
                    )
                    for (month_key, csv_txt, row_count) in batches
                ]
                for f in as_completed(futures):
                    pbar.update(f.result())
        else:
            speed_tweaks = ["SET LOCAL synchronous_commit = off", "SET LOCAL wal_compression = on"]
            for month_key, csv_txt, row_count in batches:
                staging_table = f"{staging_prefix}_{month_key.replace('-', '_')}_{uuid4().hex[:8]}"

                create_staging_sql = f'CREATE UNLOGGED TABLE {staging_table} (LIKE "{schema}"."{table_name}");'
                copy_columns = ", ".join(cols)
                copy_sql = f"COPY {staging_table} ({copy_columns}) FROM STDIN WITH (FORMAT csv, HEADER true);"
                upsert_sql = _build_insert_sql(
                    target_table=f'"{schema}"."{table_name}"',
                    staging_table=staging_table,
                    cols=cols,
                    unique_keys=unique_keys,
                    insertion_mode=batch_insertion_mode,
                )

                with db.engine.begin() as conn:
                    conn.execute(text(create_staging_sql))
                    for stmt in speed_tweaks:
                        conn.execute(text(stmt))
                    raw = getattr(conn.connection, "connection", None) or getattr(
                        conn.connection, "driver_connection", None
                    )
                    cur = raw.cursor()
                    cur.copy_expert(copy_sql, StringIO(csv_txt))

                rows_to_upsert = row_count
                skipped_rows = 0

                with db.engine.begin() as conn:
                    for stmt in speed_tweaks:
                        conn.execute(text(stmt))
                    if effective_strategy is TimeDataStrategy.UPDATE:
                        skipped_rows = _delete_identical_rows(
                            conn,
                            staging_table,
                            f'"{schema}"."{table_name}"',
                            unique_keys=unique_keys,
                            all_columns=cols,
                        )
                        rows_to_upsert = _table_rowcount(conn, staging_table)

                    if rows_to_upsert == 0:
                        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))
                    else:
                        conn.execute(text(upsert_sql))
                        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))

                if effective_strategy is TimeDataStrategy.UPDATE:
                    if rows_to_upsert == 0:
                        logger.info("Month %s: identical data found, skipping upsert", month_key)
                    elif skipped_rows:
                        logger.info(
                            "Month %s: skipped %d identical rows, upserting %d rows",
                            month_key,
                            skipped_rows,
                            rows_to_upsert,
                        )

                pbar.update(row_count)





# =========================
# Chunk comparison utilities for TimescaleDB
# =========================
def _get_affected_chunks(db, table_name: str, min_date, max_date) -> pl.DataFrame:
    """Get TimescaleDB chunk information for the given time range."""
    with db.engine.begin() as conn:
        query = text(f"""
            SELECT
                chunk_schema,
                chunk_name,
                range_start::date as chunk_start,
                range_end::date as chunk_end
            FROM timescaledb_information.chunks
            WHERE hypertable_name = '{table_name}'
              AND range_start <= CAST(:max_date AS timestamp)
              AND range_end >= CAST(:min_date AS timestamp)
            ORDER BY range_start
        """)

        result = conn.execute(query, {
            "min_date": str(min_date),
            "max_date": str(max_date)
        }).fetchall()

        if not result:
            return pl.DataFrame(schema={
                "chunk_schema": pl.Utf8,
                "chunk_name": pl.Utf8,
                "chunk_start": pl.Date,
                "chunk_end": pl.Date
            })

        return pl.DataFrame([
            {
                "chunk_schema": row[0],
                "chunk_name": row[1],
                "chunk_start": row[2],
                "chunk_end": row[3]
            }
            for row in result
        ])


def _get_chunk_data(db, model_cls, chunk_start, chunk_end, time_column: str) -> pl.DataFrame:
    """Read compressed data from a specific chunk time range."""
    table_metadata = _get_table_metadata(model_cls)
    schema, table_name, _, _, _, table_columns, _ = table_metadata

    with db.engine.begin() as conn:
        table = model_cls.__table__
        time_column_obj = getattr(table.c, time_column)
        selected_columns = [getattr(table.c, column_name) for column_name in table_columns]

        statement = (
            select(*selected_columns)
            .where(time_column_obj >= bindparam("chunk_start"))
            .where(time_column_obj < bindparam("chunk_end"))
            .order_by(time_column_obj)
        )

        params = {}
        for key, raw_value in {"chunk_start": chunk_start, "chunk_end": chunk_end}.items():
            if hasattr(raw_value, "item"):
                raw_value = raw_value.item()
            params[key] = raw_value

        rows = conn.execute(statement, params).mappings().all()

        if not rows:
            return pl.DataFrame(schema=dict.fromkeys(table_columns, pl.Utf8))

        data = [dict(row) for row in rows]
        df = pl.DataFrame(data)
        # Ensure column order matches table definition for deterministic comparisons
        return df.select([col for col in table_columns if col in df.columns])