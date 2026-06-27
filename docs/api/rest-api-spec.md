# Spécification API REST — v1

**Base URL :** `https://api.digitaltwinfactory.io/api/v1`  
**Format :** JSON  
**Auth :** Bearer JWT (sauf endpoints publics)  
**Versioning :** URL path `/v1`

---

## Authentification

### POST `/auth/register`
Créer un tenant et un utilisateur admin.

```json
// Request
{
  "email": "admin@factory.com",
  "password": "SecurePass123!",
  "first_name": "Jean",
  "last_name": "Dupont",
  "organization_name": "Usine Dupont"
}

// Response 201
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "admin@factory.com",
    "tenant_id": "uuid",
    "roles": ["tenant_admin"]
  }
}
```

### POST `/auth/login`
```json
// Request
{ "email": "admin@factory.com", "password": "SecurePass123!" }

// Response 200 — same as register
```

### POST `/auth/refresh`
```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{ "access_token": "eyJ...", "refresh_token": "eyJ...", "expires_in": 900 }
```

### POST `/auth/logout`
```json
// Request (authenticated)
{ "refresh_token": "eyJ..." }

// Response 204
```

---

## Factories

### GET `/factories`
Liste les usines du tenant.

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter: ACTIVE, INACTIVE |
| `page` | int | Page (default 1) |
| `size` | int | Page size (default 20, max 100) |

```json
// Response 200
{
  "items": [
    {
      "id": "uuid",
      "name": "Usine Nord",
      "location": "Lyon, France",
      "status": "ACTIVE",
      "machine_count": 12,
      "active_alerts": 2,
      "created_at": "2025-06-01T08:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

### POST `/factories`
Permission : `factory:write`

```json
// Request
{
  "name": "Usine Nord",
  "location": "Lyon, France",
  "config": {
    "timezone": "Europe/Paris",
    "shift_hours": [6, 14, 22]
  }
}
```

### GET `/factories/{factory_id}`
### PUT `/factories/{factory_id}`
### DELETE `/factories/{factory_id}`

---

## Production Lines

### GET `/factories/{factory_id}/lines`
### POST `/factories/{factory_id}/lines`

```json
// Request
{ "name": "Ligne A", "capacity": 500 }
```

---

## Machines

### GET `/machines`
| Param | Type | Description |
|-------|------|-------------|
| `factory_id` | uuid | Filter par usine |
| `status` | string | RUNNING, FAILURE, etc. |
| `type` | string | CNC_MILL, etc. |

### POST `/machines`
Permission : `machine:write`

```json
// Request
{
  "production_line_id": "uuid",
  "name": "CNC-001",
  "machine_type": "CNC_MILL",
  "failure_rate": 0.001,
  "nominal_production_rate": 100,
  "simulation_config": {
    "temperature": { "base": 45.0, "noise_std": 2.0 },
    "vibration": { "base": 1.5, "noise_std": 0.3 },
    "power": { "nominal_kw": 25.0 },
    "production": { "nominal_rate": 100, "unit": "pieces/min" }
  }
}
```

### GET `/machines/{machine_id}`
### PUT `/machines/{machine_id}`
### DELETE `/machines/{machine_id}`

### POST `/machines/{machine_id}/start` — Démarrer simulation
### POST `/machines/{machine_id}/stop` — Arrêter simulation

---

## Metrics

### GET `/machines/{machine_id}/metrics`
Permission : `metric:read`

| Param | Type | Description |
|-------|------|-------------|
| `from` | datetime | Début période |
| `to` | datetime | Fin période |
| `interval` | string | raw, 1m, 5m, 1h |

```json
// Response 200
{
  "machine_id": "uuid",
  "metrics": [
    {
      "temperature": 47.3,
      "vibration": 1.8,
      "power_consumption": 24.5,
      "production_rate": 98.2,
      "machine_status": "RUNNING",
      "recorded_at": "2025-06-27T10:30:01Z"
    }
  ],
  "aggregates": {
    "temperature_avg": 46.8,
    "temperature_max": 52.1,
    "vibration_avg": 1.7
  }
}
```

### GET `/machines/{machine_id}/metrics/latest`
Retourne la dernière métrique (Redis cache, < 5ms).

### GET `/machines/{machine_id}/metrics/export`
Export CSV/JSON. Params : `from`, `to`, `format`.

---

## Alerts

### GET `/alerts`
| Param | Type | Description |
|-------|------|-------------|
| `severity` | string | INFO, WARNING, CRITICAL |
| `is_resolved` | bool | false pour actives |
| `machine_id` | uuid | Filter machine |

### PATCH `/alerts/{alert_id}/acknowledge`
Permission : `alert:write`

### PATCH `/alerts/{alert_id}/resolve`
```json
{ "resolution": "Remplacement pièce usée" }
```

---

## Predictions

### GET `/machines/{machine_id}/predictions`
Permission : `prediction:read`

```json
// Response 200
{
  "predictions": [
    {
      "id": "uuid",
      "prediction_type": "FAILURE_WITHIN_24H",
      "confidence": 0.87,
      "predicted_at": "2025-06-27T10:00:00Z",
      "valid_until": "2025-06-28T10:00:00Z"
    }
  ]
}
```

---

## Maintenance

### GET `/maintenance`
### POST `/maintenance`
### PATCH `/maintenance/{id}/start`
### PATCH `/maintenance/{id}/complete`

---

## Simulation (What-if)

### POST `/simulation/what-if`
Permission : `simulation:write`

```json
// Request
{
  "machine_id": "uuid",
  "overrides": {
    "production_rate_multiplier": 1.2,
    "temperature_base": 55.0
  },
  "duration_hours": 24
}

// Response 200
{
  "scenario_id": "uuid",
  "projected_metrics": {
    "failure_probability_24h": 0.34,
    "avg_temperature": 58.2,
    "avg_production_rate": 118.5
  },
  "recommendation": "Risque panne élevé — réduire cadence à 110%",
  "expires_at": "2025-06-27T11:30:00Z"
}
```

---

## Users & RBAC

### GET `/users` — Permission : `user:read`
### POST `/users` — Permission : `user:write`
### GET `/roles`
### POST `/users/{id}/roles` — Assign role

---

## Health & Monitoring

### GET `/health` — Public
```json
{ "status": "healthy", "version": "1.0.0", "services": { "db": "ok", "redis": "ok" } }
```

### GET `/metrics` — Prometheus format (interne)

---

## Codes d'erreur standard

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Données invalides |
| `UNAUTHORIZED` | 401 | Token absent/invalid |
| `FORBIDDEN` | 403 | Permission insuffisante |
| `NOT_FOUND` | 404 | Ressource introuvable |
| `CONFLICT` | 409 | Email/slug déjà existant |
| `RATE_LIMITED` | 429 | Trop de requêtes |
| `INTERNAL_ERROR` | 500 | Erreur serveur |

```json
// Format erreur
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "email is required",
    "details": [{ "field": "email", "message": "required" }],
    "correlation_id": "abc-123"
  }
}
```
