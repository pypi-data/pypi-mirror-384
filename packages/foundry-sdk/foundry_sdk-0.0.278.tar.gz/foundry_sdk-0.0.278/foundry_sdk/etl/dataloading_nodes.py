# import typing as t
from datetime import date, datetime

import polars as pl

from foundry_sdk.db_mgmt.sql_db_alchemy import SQLAlchemyDatabase

from .dataloader import DataLoader
from .validation import DataValidator

#########################################################################################################
#################################### Write nodes ########################################################
#########################################################################################################

#################################### Data input validation ########################################

def node_sync_regions(
    data_loader: DataLoader,
) -> bool:
    return data_loader.sync_regions()

def check_data_inputs(
    company_name: str,
    dataset_type: str,
    min_date: datetime | date,
    max_date: datetime | date,
    frequency: int,
    store_region_map: pl.DataFrame,
    categories_dict: dict,
    categories_level_description: pl.DataFrame,
    products: pl.DataFrame,
    sales_data_map: pl.DataFrame,
    flags: pl.DataFrame,
    store_feature_description_map: pl.DataFrame,
    store_feature_map: pl.DataFrame,
    product_feature_description_map: pl.DataFrame,
    product_feature_map: pl.DataFrame,
    sku_feature_description_map: pl.DataFrame,
    sku_feature_map: pl.DataFrame,
    time_product_feature_description_map: pl.DataFrame,
    time_product_feature_map: pl.DataFrame,
    time_region_feature_description_map: pl.DataFrame,
    time_region_feature_map: pl.DataFrame,
    time_store_feature_description_map: pl.DataFrame,
    time_store_feature_map: pl.DataFrame,
    time_sku_data: pl.DataFrame,
    time_sku_feature_description_map: pl.DataFrame,
    regions_synced: bool,
    ) -> bool:
    # Data validation logic will be implemented here

    if not regions_synced:
        raise ValueError("Regions must be synced before data validation can proceed.")

    db = SQLAlchemyDatabase.from_kedro()

    # Check if regions table is empty and sync from general database if needed
    from foundry_sdk.db_mgmt.tables_general_data import Regions as GeneralRegions
    from foundry_sdk.db_mgmt.tables_ts import Regions as TSRegions
    from foundry_sdk.db_mgmt.utils.cross_db_ops import copy_table_data, is_table_empty

    # if is_table_empty(db, TSRegions):
    #     general_db = SQLAlchemyDatabase.from_kedro(credentials_name="postgres_general_data")
    #     copy_table_data(general_db, db, GeneralRegions, TSRegions)

    with DataValidator(db) as data_validator:
        data_validator.check_company_name(company_name)
        data_validator.check_dataset_type(dataset_type, company_name)
        data_validator.check_date_range(min_date, max_date)
        data_validator.check_frequency(frequency)
        data_validator.check_store_region_map(store_region_map)
        data_validator.check_products_and_categories(categories_dict, categories_level_description, products)
        data_validator.check_sales(sales_data_map)
        data_validator.check_time_sku_data(
            time_sku_feature_description_map,
            time_sku_data,
        )
        data_validator.check_flags(flags, sales_data_map)
        data_validator.check_feature_descriptions(
            time_sku_feature_description_map,
            store_feature_description_map,
            product_feature_description_map,
            sku_feature_description_map,
            time_product_feature_description_map,
            time_region_feature_description_map,
            time_store_feature_description_map,
        )
        data_validator.check_store_feature_data(store_feature_description_map, store_feature_map)
        data_validator.check_product_feature_data(product_feature_description_map, product_feature_map)
        data_validator.check_sku_feature_data(sku_feature_description_map, sku_feature_map)
        data_validator.check_time_product_feature_data(time_product_feature_description_map, time_product_feature_map)
        data_validator.check_time_region_feature_data(time_region_feature_description_map, time_region_feature_map)
        data_validator.check_time_store_feature_data(time_store_feature_description_map, time_store_feature_map)

    return True


#################################### Mandatory data ############################################


def node_write_company(
    data_loader: DataLoader,
    company_name: str,
    dataset_type: str,
    description: str,
    min_date: datetime | date,
    max_date: datetime | date,
    frequency: int,
    *,
    check_passed: bool,
    regions_synced: bool,
) -> int:
    return data_loader.write_company(
        company_name, dataset_type, description, min_date, max_date, frequency, check_passed=check_passed, regions_synced=regions_synced
    )




def node_write_stores(
    data_loader: DataLoader,
    store_region_map: pl.DataFrame,
    company_id: int,
    *,
    check_passed: bool,
) -> pl.DataFrame:
    return data_loader.write_stores(store_region_map, company_id, check_passed=check_passed)


def node_write_categories(
    data_loader: DataLoader,
    categories_dict: dict,
    level_names: pl.DataFrame,
    company_id: int,
    *,
    check_passed: bool,
) -> pl.DataFrame:
    return data_loader.write_categories(categories_dict, level_names, company_id, check_passed=check_passed)


def node_write_products(
    data_loader: DataLoader,
    products: pl.DataFrame,
    company_id: int,
    *,
    check_passed: bool,
) -> pl.DataFrame:
    return data_loader.write_products(products, company_id, check_passed=check_passed)


def node_write_product_categories(
    data_loader: DataLoader,
    products: pl.DataFrame,
    category_ids: pl.DataFrame,
    product_ids: pl.DataFrame,
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_product_categories(
        products,
        product_ids,
        category_ids,
        check_passed=check_passed,
    )


def node_write_skus(
    data_loader: DataLoader,
    sales_data_map: pl.DataFrame,
    store_ids: pl.DataFrame,
    product_ids: pl.DataFrame,
    company_id: int,
    *,
    check_passed: bool,
) -> pl.DataFrame:
    return data_loader.write_skus(sales_data_map, store_ids, product_ids, company_id, check_passed=check_passed)


def node_write_sales(
    data_loader: DataLoader,
    sales: pl.DataFrame,
    sku_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    time_data_strategy: dict[str, str],
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_sales(
        sales,
        sku_ids,
        company_id,
        check_passed=check_passed,
        strategy=time_data_strategy["sales"],
        num_workers=num_workers,
    )


def node_write_flags(
    data_loader: DataLoader,
    flags: pl.DataFrame,
    sku_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    time_data_strategy: dict[str, str],
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_flags(
        flags,
        sku_ids,
        company_id,
        check_passed=check_passed,
        strategy=time_data_strategy["flags"],
        num_workers=num_workers,
    )


# #################################### Optional data #############################################


def node_write_store_data(
    data_loader: DataLoader,
    store_feature_description_map: pl.DataFrame,
    store_feature_map: pl.DataFrame,
    store_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_store_data(
        store_feature_description_map, 
        store_feature_map, 
        store_ids, 
        company_id, 
        check_passed=check_passed,
        num_workers=num_workers,
    )


def node_write_product_data(
    data_loader: DataLoader,
    product_feature_description_map: pl.DataFrame,
    product_feature_map: pl.DataFrame,
    product_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_product_data(
        product_feature_description_map, 
        product_feature_map, 
        product_ids, 
        company_id, 
        check_passed=check_passed,
        num_workers=num_workers,
    )


def node_write_sku_data(
    data_loader: DataLoader,
    sku_feature_description_map: pl.DataFrame,
    sku_feature_map: pl.DataFrame,
    sku_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_sku_data(
        sku_feature_description_map, 
        sku_feature_map, 
        sku_ids, 
        company_id, 
        check_passed=check_passed,
        num_workers=num_workers,
    )


def node_write_time_product_data(
    data_loader: DataLoader,
    time_product_feature_description_map: pl.DataFrame,
    time_product_feature_map: pl.DataFrame,
    product_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    time_data_strategy: dict[str, str],
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_time_product_data(
        time_product_feature_description_map,
        time_product_feature_map,
        product_ids,
        company_id,
        check_passed=check_passed,
        strategy=time_data_strategy["time_product_data"],
        num_workers=num_workers,
    )


def node_write_time_region_data(
    data_loader: DataLoader,
    time_region_feature_description_map: pl.DataFrame,
    time_region_feature_map: pl.DataFrame,
    company_id: int,
    num_workers: int,
    time_data_strategy: str,
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_time_region_data(
        time_region_feature_description_map,
        time_region_feature_map,
        company_id,
        check_passed=check_passed,
        strategy=time_data_strategy["time_region_data"],
        num_workers=num_workers,
    )


def node_write_time_store_data(
    data_loader: DataLoader,
    time_store_feature_description_map: pl.DataFrame,
    time_store_feature_map: pl.DataFrame,
    store_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    time_data_strategy: str,
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_time_store_data(
        time_store_feature_description_map,
        time_store_feature_map,
        store_ids,
        company_id,
        check_passed=check_passed,
        num_workers=num_workers,
        strategy=time_data_strategy["time_store_data"],
    )


def node_write_time_sku_data(
    data_loader: DataLoader,
    time_sku_feature_description_map: pl.DataFrame,
    time_sku_data: pl.DataFrame,
    sku_ids: pl.DataFrame,
    company_id: int,
    num_workers: int,
    time_data_strategy: dict[str, str],
    *,
    check_passed: bool,
) -> bool:
    return data_loader.write_time_sku_data(
        time_sku_feature_description_map,
        time_sku_data,
        sku_ids,
        company_id,
        check_passed=check_passed,
        strategy=time_data_strategy["time_sku_data"],
        num_workers=num_workers,
    )
