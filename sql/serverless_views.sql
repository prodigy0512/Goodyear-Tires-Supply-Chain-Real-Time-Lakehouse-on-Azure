-- Synapse Serverless example
-- Create external data source + file format separately.
-- Then create views over the GOLD parquet.

CREATE OR ALTER VIEW vw_kpi_inventory_health AS
SELECT *
FROM OPENROWSET(
    BULK 'gold/kpi_inventory_health/*/*.parquet',
    DATA_SOURCE = 'ds_goodyear_adls',
    FORMAT = 'PARQUET'
) WITH (
    snapshot_date date,
    plant_id varchar(20),
    total_on_hand_qty bigint,
    skus_below_safety bigint,
    sku_count bigint,
    pct_skus_below_safety float
) AS rows;
