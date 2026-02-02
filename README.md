# Goodyear Tires Supply Chain – Real‑Time Lakehouse on Azure (ADF + ADLS Gen2)

A GitHub-ready, portfolio-grade data engineering project that simulates a **critical supply chain management system** for a tire manufacturer.
It demonstrates how to ingest data from **on‑prem systems** and **cloud Oracle**, land it into **Azure Data Lake Storage Gen2 (ADLS)**,
transform it into curated layers, and publish analytics-ready models — with **CI/CD**, **security**, **monitoring**, and **data governance**.

> ✅ Designed for recruiters/interviewers: clean repo structure, realistic datasets, infra-as-code, and deploy/run instructions.

---

## Architecture (high level)

**Sources**
- On‑prem ERP / MES (simulated): SQL Server (plants, inventory, production)
- Cloud Oracle (simulated): supplier master, purchase orders
- Streaming events (simulated): shipment status + IoT telemetry

**Ingestion**
- Azure Data Factory (ADF) pipelines
- Self-hosted Integration Runtime (SHIR) for on‑prem connectivity
- Managed VNet + Managed Private Endpoints for private access (optional hardening)

**Storage**
- ADLS Gen2 with layered zones:
  - `bronze/` raw immutable
  - `silver/` cleaned & conformed
  - `gold/` business marts (OTIF, inventory health, lead time, backorders)

**Transform**
- Mapping Data Flows (ADF) for light cleansing
- Spark (Databricks/Synapse) notebooks for heavy transforms & SCD2

**Serve**
- Synapse Serverless SQL views / External tables (optional)
- Power BI semantic model (not included; see guide)

**Governance**
- Microsoft Purview lineage from ADF pipelines

**Observability**
- ADF diagnostics → Log Analytics
- Alerts for pipeline failure, latency, data quality drift

---

## What you can demo in interviews (talk track)

1. **Real-time-ish ingestion**: shipment events land every minute, batch ERP data hourly.
2. **Medallion architecture**: bronze→silver→gold with idempotent loads.
3. **SCD Type 2**: Supplier & product attributes tracked over time.
4. **KPIs**: OTIF, fill rate, inventory turnover, lead time, backorder aging.
5. **Enterprise practices**: Key Vault secrets, RBAC, private connectivity, CI/CD.

---

## Repo structure

```
.
├── adf/                         # ADF factory resources (pipelines/datasets/linked services)
├── infra/                       # Bicep IaC to deploy Azure resources
├── data/                        # Synthetic data generator + sample files
├── notebooks/                   # PySpark transformations + data quality checks
├── sql/                         # Serverless SQL views (optional)
├── cicd/                        # GitHub Actions templates + release notes
└── docs/                        # Diagrams + screenshots (placeholders)
```

---

## Quickstart (local)

You can **generate realistic sample data** locally:

```bash
python data/generate_data.py --out data/sample_out --days 30 --plants 3
```

This creates CSV/JSON data you can upload to ADLS to simulate sources.

---

## Deploy (Azure) – two modes

### Mode A (Portfolio-friendly, easiest)
Deploy core services publicly (still using Key Vault + RBAC):
1. Deploy infra via Bicep
2. Create ADF linked services
3. Import ADF resources from `/adf` folder
4. Run triggers

### Mode B (Enterprise hardening, private networking)
Adds ADF **Managed VNet + Managed Private Endpoints** and locks down Storage/Key Vault.
This follows Microsoft guidance for private link patterns.

See: `infra/README.md`

---

## CI/CD (recommended)
- Use Git integration in ADF for dev only
- Publish generates ARM templates to the publish branch
- A release pipeline deploys ARM templates to test/prod

Microsoft docs on ADF CI/CD explain this flow.

---

## Screenshots you should add (to impress)
1. ADF pipeline run history
2. ADLS container showing bronze/silver/gold folders
3. Purview lineage graph
4. Power BI dashboard page (OTIF + inventory)

Place them in `docs/screenshots/`.

---

## License
MIT
