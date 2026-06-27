# Cas d'utilisation — Digital Twin Factory

## UC-01 — Inscription et création de tenant

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-01 |
| **Acteur** | Nouvel utilisateur |
| **Précondition** | Email non existant |
| **Postcondition** | Tenant + User admin créés, JWT retourné |

**Flux principal :**
1. Utilisateur soumet email, password, nom organisation
2. Système crée `Tenant` avec slug unique
3. Système crée `User` avec rôle `tenant_admin`
4. Système émet `TenantCreated`, `UserRegistered`
5. Système retourne access + refresh token

**Flux alternatif — Email existant :**
- Retourne `409 Conflict`

---

## UC-02 — Authentification JWT

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-02 |
| **Acteur** | Utilisateur authentifié |
| **Précondition** | Compte actif |
| **Postcondition** | JWT access (15min) + refresh (7j) |

**Flux principal :**
1. POST `/api/v1/auth/login` avec email + password
2. Vérification bcrypt du password
3. Génération access token (permissions incluses)
4. Génération refresh token, stockage jti en Redis
5. Émission `UserLoggedIn` event
6. Retour tokens + user info

**Sécurité :**
- Rate limit : 5 tentatives/min/IP
- Account lockout après 10 échecs (15 min)
- Log audit de chaque tentative

---

## UC-03 — Créer une usine

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-03 |
| **Acteur** | Admin Tenant |
| **Permission** | `factory:write` |
| **Postcondition** | Factory créée, event `FactoryCreated` |

**Flux principal :**
1. POST `/api/v1/factories` avec name, location, config
2. Validation : name non vide, tenant_id du JWT
3. Création aggregate `Factory`
4. Persistance via Repository + Unit of Work
5. Émission `FactoryCreated`
6. Retour factory DTO

---

## UC-04 — Provisionner une machine virtuelle

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-04 |
| **Acteur** | Admin Tenant |
| **Permission** | `machine:write` |
| **Postcondition** | Machine créée, simulation démarrée |

**Flux principal :**
1. POST `/api/v1/machines` avec type, config simulation
2. Validation type machine + config JSONB
3. Création aggregate `Machine` avec `simulation_config`
4. Émission `MachineProvisioned`
5. Policy `StartSimulationOnProvision` → Celery task
6. Retour machine DTO

**Types de machines supportés :**
`CNC_MILL`, `ROBOT_ARM`, `CONVEYOR`, `PRESS`, `WELDER`, `PACKAGING`

---

## UC-05 — Observer le dashboard temps réel

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-05 |
| **Acteur** | Opérateur |
| **Permission** | `metric:read` |
| **Postcondition** | Stream métriques live < 100ms latence |

**Flux principal :**
1. Client connecte WS `/ws/factory/{factory_id}?token=jwt`
2. API valide JWT + permission + tenant_id
3. API subscribe Redis `factory:{id}:metrics`
4. Chaque tick simulation → Redis PUBLISH
5. API forward JSON au client WebSocket
6. Client affiche métriques live

**Format message WebSocket :**
```json
{
  "event": "metric",
  "machine_id": "uuid",
  "data": {
    "temperature": 47.3,
    "vibration": 1.8,
    "power_consumption": 24.5,
    "production_rate": 98.2,
    "status": "RUNNING"
  },
  "timestamp": "2025-06-27T10:30:01Z"
}
```

---

## UC-06 — Déclencher et gérer une alerte

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-06 |
| **Acteur** | Système + Opérateur |
| **Permission** | `alert:read`, `alert:write` |

**Flux automatique (Système) :**
1. `MetricGenerated` → check `threshold_rules`
2. Si seuil dépassé → `AlertRaised`
3. PUBLISH Redis `factory:{id}:alerts`
4. Si CRITICAL → `NotificationSent` immédiat

**Flux manuel (Opérateur) :**
1. GET `/api/v1/alerts?status=active`
2. PATCH `/api/v1/alerts/{id}/acknowledge`
3. Émission `AlertAcknowledged`

---

## UC-07 — Maintenance prédictive

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-07 |
| **Acteur** | Système (Celery) + Ingénieur maintenance |
| **Permission** | `prediction:read`, `maintenance:write` |

**Flux automatique :**
1. Celery `aggregate_metrics` (5 min) → `MetricsAggregated`
2. Celery `detect_anomalies` → score > 0.7 → `AnomalyDetected`
3. Celery `run_failure_prediction` → confidence > 0.8 → `FailurePredicted`
4. `MaintenanceScheduled` créé automatiquement
5. Notification envoyée à ingénieur maintenance

**Flux manuel :**
1. GET `/api/v1/predictions/{machine_id}`
2. GET `/api/v1/maintenance?status=scheduled`
3. PATCH `/api/v1/maintenance/{id}/complete`

---

## UC-08 — What-if Scenario (différenciateur)

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-08 |
| **Acteur** | Ingénieur maintenance |
| **Permission** | `simulation:write` |

**Description :** Simuler l'impact d'un changement de paramètres sans affecter la production réelle.

**Flux :**
1. POST `/api/v1/simulation/what-if` avec machine_id + paramètres modifiés
2. Moteur simulation fork temporaire (pas de persistance)
3. Retour prédiction impact sur 24h : métriques projetées, risque panne
4. Résultat expire après 1h (Redis TTL)

---

## UC-09 — Export métriques

| Attribut | Valeur |
|----------|--------|
| **ID** | UC-09 |
| **Acteur** | Data Scientist |
| **Permission** | `metric:read` |

**Flux :**
1. GET `/api/v1/machines/{id}/metrics/export?from=&to=&format=csv`
2. Query handler avec pagination
3. Export CSV ou JSON des métriques historiques
4. Rate limit : 10 exports/heure

---

## Matrice Acteurs × Use Cases

| UC | Super Admin | Tenant Admin | Operator | Maintenance Eng. | Viewer |
|----|:-----------:|:------------:|:--------:|:----------------:|:------:|
| UC-01 Inscription | ✓ | ✓ | ✓ | ✓ | ✓ |
| UC-02 Login | ✓ | ✓ | ✓ | ✓ | ✓ |
| UC-03 Créer usine | ✓ | ✓ | ✗ | ✗ | ✗ |
| UC-04 Provisionner machine | ✓ | ✓ | ✗ | ✗ | ✗ |
| UC-05 Dashboard live | ✓ | ✓ | ✓ | ✓ | ✓ |
| UC-06 Gérer alertes | ✓ | ✓ | ✓ | ✓ | ✗ |
| UC-07 Maintenance prédictive | ✓ | ✓ | ✗ | ✓ | ✗ |
| UC-08 What-if | ✓ | ✓ | ✗ | ✓ | ✗ |
| UC-09 Export métriques | ✓ | ✓ | ✗ | ✓ | ✗ |
