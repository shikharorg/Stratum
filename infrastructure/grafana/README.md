# Stratum Grafana Dashboards

Two dashboards for the Stratum AI Operations Platform.

## Dashboards

### Stratum Platform Overview (`stratum-platform-overview.json`)
Business-level metrics from PostgreSQL databases. Refreshes every 30s, default range: last 7 days.

| Panel | Source | Query |
|-------|--------|-------|
| Documents Ingested | Stratum Ingestion | `COUNT(*) WHERE status='completed'` |
| Total Searches | Stratum Retrieval | `COUNT(*)` on retrieval_logs |
| Total Workflow Runs | Stratum Workflow | `COUNT(*)` on workflow_runs |
| Avg RAG Score | Stratum Evaluation | `AVG(overall_score)` |
| Avg Faithfulness (gauge) | Stratum Evaluation | `AVG(faithfulness)` |
| Avg Answer Relevancy (gauge) | Stratum Evaluation | `AVG(answer_relevancy)` |
| Avg Context Precision (gauge) | Stratum Evaluation | `AVG(context_precision)` |
| RAG Score Over Time | Stratum Evaluation | `overall_score` time series |
| Search Latency (ms) | Stratum Retrieval | `latency_ms` time series |

### Stratum Infrastructure (`stratum-infrastructure.json`)
HTTP request rates and latency from Prometheus. Refreshes every 15s, default range: last 1 hour.

| Panel | Source | Query |
|-------|--------|-------|
| Per-service stat (×8) | Prometheus | `rate(http_requests_total{job="<service>"}[5m])` |
| P95 Latency by Service | Prometheus | `histogram_quantile(0.95, ...)` |
| 5xx Error Rate | Prometheus | `rate(http_requests_total{status=~"5.."}[5m])` |

## Required Datasources

Create these in Grafana → Connections → Data Sources before importing:

| Name | Type | Host | Database | User | Password |
|------|------|------|----------|------|----------|
| Stratum Evaluation | PostgreSQL | `stratum-postgres:5432` | `stratum_evaluation` | `stratum` | `stratum_dev` |
| Stratum Retrieval | PostgreSQL | `stratum-postgres:5432` | `stratum_retrieval` | `stratum` | `stratum_dev` |
| Stratum Ingestion | PostgreSQL | `stratum-postgres:5432` | `stratum_ingestion` | `stratum` | `stratum_dev` |
| Stratum Workflow | PostgreSQL | `stratum-postgres:5432` | `stratum_workflow` | `stratum` | `stratum_dev` |
| prometheus | Prometheus | `http://stratum-prometheus:9090` | — | — | — |

For all PostgreSQL sources: SSL Mode = `disable`, PostgreSQL Version = `15`.

## Importing Dashboards

### Option A — Grafana API (scripted)

```bash
# Add datasources first (adjust passwords for non-dev environments)
for DB in stratum_evaluation stratum_retrieval stratum_ingestion stratum_workflow; do
  NAME=$(echo $DB | sed 's/stratum_/Stratum /' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2)); print}')
  curl -s -u admin:stratum_admin -X POST http://localhost:3000/api/datasources \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$NAME\",\"type\":\"grafana-postgresql-datasource\",\"url\":\"stratum-postgres:5432\",\"access\":\"proxy\",\"database\":\"$DB\",\"user\":\"stratum\",\"secureJsonData\":{\"password\":\"stratum_dev\"},\"jsonData\":{\"sslmode\":\"disable\",\"postgresVersion\":1500},\"basicAuth\":false}"
done

# Import dashboards
for FILE in stratum-platform-overview.json stratum-infrastructure.json; do
  curl -s -u admin:stratum_admin -X POST http://localhost:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -d @infrastructure/grafana/$FILE
done
```

### Option B — Grafana UI

1. Open Grafana → Dashboards → Import
2. Upload each JSON file
3. Map datasource variables to the datasources created above
4. Click Import

## Dashboard UIDs

The JSON files ship with fixed UIDs so re-imports are idempotent (they update rather than duplicate):

- Platform Overview: `82dbb5ca-e5a2-44f2-889f-3ebd76aa99c3`
- Infrastructure: `c3be42fb-7cca-4123-8166-2395d7445326`
