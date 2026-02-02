# Infra (Bicep) – What gets deployed

This folder contains Bicep templates to deploy a realistic stack:

- Azure Data Factory
- ADLS Gen2 Storage Account (hierarchical namespace)
- Key Vault
- Log Analytics Workspace (for ADF diagnostics)
- (Optional) Microsoft Purview account (governance)
- (Optional) Event Hub namespace (stream ingestion)

> Note: Purview + private endpoints may require additional permissions/quotas in your subscription.

## Deploy

```bash
az login
az account set --subscription <SUBSCRIPTION_ID>
az group create -n rg-goodyear-supplychain -l eastus
az deployment group create -g rg-goodyear-supplychain -f main.bicep -p params.dev.json
```

## Private networking hardening

ADF supports **Managed Virtual Network** and **Managed Private Endpoints** for supported stores.
See Microsoft guidance:
- Managed VNet + private endpoint concepts
- Data access strategies (Private Link)

In portfolio mode you can keep networking simple and focus on pipelines/transform/serving.
