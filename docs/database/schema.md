# Modèle Relationnel — PostgreSQL

## Diagramme ERD

```mermaid
erDiagram
    tenants ||--o{ users : has
    tenants ||--o{ factories : owns
    factories ||--o{ production_lines : contains
    production_lines ||--o{ machines : contains
    machines ||--o{ machine_metrics : generates
    machines ||--o{ alerts : triggers
    machines ||--o{ maintenance_records : requires
    machines ||--o{ predictions : receives
    machines ||--o{ threshold_rules : configures
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : assigned_to
    roles ||--o{ role_permissions : has
    permissions ||--o{ role_permissions : granted_to
    alerts ||--o{ notifications : triggers
    users ||--o{ notifications : receives

    tenants {
        uuid id PK
        varchar name
        varchar slug UK
        jsonb settings
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    users {
        uuid id PK
        uuid tenant_id FK
        varchar email UK
        varchar password_hash
        varchar first_name
        varchar last_name
        boolean is_active
        timestamptz last_login
        timestamptz created_at
        timestamptz updated_at
    }

    roles {
        uuid id PK
        varchar name UK
        varchar description
        boolean is_system
        timestamptz created_at
    }

    permissions {
        uuid id PK
        varchar name UK
        varchar resource
        varchar action
        varchar description
    }

    user_roles {
        uuid user_id FK
        uuid role_id FK
        timestamptz assigned_at
    }

    role_permissions {
        uuid role_id FK
        uuid permission_id FK
    }

    factories {
        uuid id PK
        uuid tenant_id FK
        varchar name
        varchar location
        varchar status
        jsonb config
        timestamptz created_at
        timestamptz updated_at
    }

    production_lines {
        uuid id PK
        uuid factory_id FK
        varchar name
        integer capacity
        varchar status
        timestamptz created_at
        timestamptz updated_at
    }

    machines {
        uuid id PK
        uuid production_line_id FK
        uuid tenant_id FK
        varchar name
        varchar machine_type
        varchar status
        jsonb simulation_config
        float failure_rate
        float nominal_production_rate
        timestamptz created_at
        timestamptz updated_at
    }

    machine_metrics {
        uuid id PK
        uuid machine_id FK
        uuid tenant_id FK
        float temperature
        float vibration
        float power_consumption
        float production_rate
        varchar machine_status
        timestamptz recorded_at
    }

    threshold_rules {
        uuid id PK
        uuid machine_id FK
        uuid tenant_id FK
        varchar metric_name
        float warning_threshold
        float critical_threshold
        varchar comparison_operator
        boolean is_active
        timestamptz created_at
    }

    alerts {
        uuid id PK
        uuid machine_id FK
        uuid tenant_id FK
        varchar alert_type
        varchar severity
        varchar message
        jsonb metadata
        boolean is_acknowledged
        uuid acknowledged_by FK
        timestamptz acknowledged_at
        boolean is_resolved
        timestamptz resolved_at
        timestamptz created_at
    }

    predictions {
        uuid id PK
        uuid machine_id FK
        uuid tenant_id FK
        varchar prediction_type
        float confidence
        jsonb features
        timestamptz predicted_at
        timestamptz valid_until
        timestamptz created_at
    }

    maintenance_records {
        uuid id PK
        uuid machine_id FK
        uuid tenant_id FK
        uuid assigned_to FK
        varchar maintenance_type
        varchar status
        varchar description
        timestamptz scheduled_at
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }

    notifications {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        uuid alert_id FK
        varchar channel
        varchar status
        varchar subject
        text body
        jsonb metadata
        timestamptz sent_at
        timestamptz delivered_at
        timestamptz created_at
    }

    audit_logs {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        varchar action
        varchar resource_type
        uuid resource_id
        jsonb changes
        varchar ip_address
        timestamptz created_at
    }
```

## Index stratégiques

```sql
-- Multi-tenancy (toutes les tables métier)
CREATE INDEX idx_factories_tenant_id ON factories(tenant_id);
CREATE INDEX idx_machines_tenant_id ON machines(tenant_id);
CREATE INDEX idx_machine_metrics_tenant_id ON machine_metrics(tenant_id);

-- Métriques temps série (lectures fréquentes)
CREATE INDEX idx_metrics_machine_recorded ON machine_metrics(machine_id, recorded_at DESC);
CREATE INDEX idx_metrics_tenant_recorded ON machine_metrics(tenant_id, recorded_at DESC);

-- Alertes actives
CREATE INDEX idx_alerts_active ON alerts(tenant_id, is_resolved, created_at DESC)
    WHERE is_resolved = false;

-- Prédictions valides
CREATE INDEX idx_predictions_valid ON predictions(machine_id, valid_until DESC)
    WHERE valid_until > NOW();
```

## Row Level Security

```sql
ALTER TABLE factories ENABLE ROW LEVEL SECURITY;
ALTER TABLE machines ENABLE ROW LEVEL SECURITY;
ALTER TABLE machine_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_factories ON factories
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY tenant_isolation_machines ON machines
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```

## Stratégie de rétention des données

| Table | Rétention | Stratégie |
|-------|-----------|-----------|
| `machine_metrics` | 90 jours raw | Partition par mois + agrégation |
| `alerts` | 1 an | Archivage cold storage |
| `predictions` | 6 mois | — |
| `audit_logs` | 2 ans | Compliance |
| `notifications` | 30 jours | — |

## Enums PostgreSQL

```sql
CREATE TYPE factory_status AS ENUM ('ACTIVE', 'INACTIVE', 'MAINTENANCE');
CREATE TYPE machine_type AS ENUM ('CNC_MILL', 'ROBOT_ARM', 'CONVEYOR', 'PRESS', 'WELDER', 'PACKAGING');
CREATE TYPE machine_status AS ENUM ('RUNNING', 'IDLE', 'DEGRADED', 'FAILURE', 'MAINTENANCE', 'OFFLINE');
CREATE TYPE alert_severity AS ENUM ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY');
CREATE TYPE alert_type AS ENUM ('TEMPERATURE_HIGH', 'VIBRATION_CRITICAL', 'POWER_SPIKE', 'PRODUCTION_DROP', 'MACHINE_FAILURE', 'PREDICTIVE_WARNING');
CREATE TYPE prediction_type AS ENUM ('FAILURE_WITHIN_24H', 'FAILURE_WITHIN_7D', 'OVERHEAT_RISK', 'MAINTENANCE_DUE', 'ANOMALY_DETECTED');
CREATE TYPE maintenance_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
CREATE TYPE notification_channel AS ENUM ('IN_APP', 'EMAIL', 'WEBHOOK', 'SLACK');
CREATE TYPE notification_status AS ENUM ('PENDING', 'SENT', 'DELIVERED', 'FAILED');
```

## simulation_config JSONB (exemple)

```json
{
  "temperature": {
    "base": 45.0,
    "noise_std": 2.0,
    "degradation_rate": 0.001
  },
  "vibration": {
    "base": 1.5,
    "noise_std": 0.3
  },
  "power": {
    "nominal_kw": 25.0,
    "efficiency_factor": 0.92
  },
  "production": {
    "nominal_rate": 100,
    "unit": "pieces/min"
  },
  "failure": {
    "mtbf_hours": 720,
    "mttr_hours": 4
  }
}
```
