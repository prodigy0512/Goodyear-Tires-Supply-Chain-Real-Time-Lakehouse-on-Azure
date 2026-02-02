# PySpark notebook (Databricks/Synapse) - Silver & Gold transforms
# This is a script version to keep it GitHub-friendly.
# Convert CSV bronze -> parquet silver, then compute gold KPIs.

from pyspark.sql import functions as F, Window

bronze_path = "abfss://datalake@<storage-account>.dfs.core.windows.net/bronze"
silver_path = "abfss://datalake@<storage-account>.dfs.core.windows.net/silver"
gold_path   = "abfss://datalake@<storage-account>.dfs.core.windows.net/gold"

# -----------------------------
# 1) SILVER: Inventory snapshots
# -----------------------------
inv = (spark.read.option("header", True)
       .csv(f"{bronze_path}/erp/inventory_snapshot/*/*/*/inventory_snapshot.csv")
       .withColumn("snapshot_date", F.to_date("snapshot_date"))
       .withColumn("on_hand_qty", F.col("on_hand_qty").cast("int"))
       .withColumn("safety_stock_qty", F.col("safety_stock_qty").cast("int"))
       .withColumn("is_below_safety", (F.col("on_hand_qty") < F.col("safety_stock_qty")).cast("int"))
      )

(inv.write.mode("overwrite")
 .partitionBy("snapshot_date")
 .parquet(f"{silver_path}/inventory_snapshot"))

# -----------------------------
# 2) SILVER: Purchase orders
# -----------------------------
po = (spark.read.option("header", True)
      .csv(f"{bronze_path}/oracle/purchase_orders/*/*/*/purchase_orders.csv")
      .withColumn("order_date", F.to_date("order_date"))
      .withColumn("expected_delivery_date", F.to_date("expected_delivery_date"))
      .withColumn("order_qty", F.col("order_qty").cast("int"))
      .withColumn("unit_cost_usd", F.col("unit_cost_usd").cast("double"))
     )

(po.write.mode("overwrite")
 .partitionBy("order_date")
 .parquet(f"{silver_path}/purchase_orders"))

# -----------------------------
# 3) GOLD: Inventory Health KPI
# -----------------------------
gold_inventory_health = (inv.groupBy("snapshot_date", "plant_id")
    .agg(
        F.sum("on_hand_qty").alias("total_on_hand_qty"),
        F.sum("is_below_safety").alias("skus_below_safety"),
        F.countDistinct("sku").alias("sku_count"),
    )
    .withColumn("pct_skus_below_safety", F.col("skus_below_safety") / F.col("sku_count"))
)

(gold_inventory_health.write.mode("overwrite")
 .partitionBy("snapshot_date")
 .parquet(f"{gold_path}/kpi_inventory_health"))
