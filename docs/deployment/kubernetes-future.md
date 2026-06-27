# Kubernetes Deployment — Future Architecture

## Vue d'ensemble

Phase 3 — déploiement production sur Kubernetes avec auto-scaling et haute disponibilité.

```mermaid
flowchart TB
    subgraph Ingress
        Ingress[Nginx Ingress<br/>TLS termination]
    end

    subgraph API["API Namespace"]
        API1[API Pod 1]
        API2[API Pod 2]
        API3[API Pod 3]
        HPA[Horizontal Pod Autoscaler]
    end

    subgraph Workers["Workers Namespace"]
        SimW[Simulation Workers<br/>Deployment]
        MonW[Monitoring Workers]
        PredW[Prediction Workers]
        NotifW[Notification Workers]
        Beat[Celery Beat<br/>Singleton]
    end

    subgraph Data["Data Namespace"]
        PG[PostgreSQL<br/>StatefulSet + PVC]
        Redis[Redis<br/>StatefulSet + Sentinel]
    end

    subgraph Monitoring["Monitoring Namespace"]
        Prom[Prometheus]
        Graf[Grafana]
        Loki[Loki]
    end

    Ingress --> API1
    Ingress --> API2
    Ingress --> API3
    HPA --> API1
    API1 --> PG
    API1 --> Redis
    SimW --> PG
    SimW --> Redis
    Beat --> Redis
```

## Services Kubernetes

| Resource | Type | Replicas | Resources |
|----------|------|----------|-----------|
| `api` | Deployment | 2-10 (HPA) | 512Mi / 500m CPU |
| `simulation-worker` | Deployment | 2-4 | 512Mi / 500m CPU |
| `monitoring-worker` | Deployment | 1-2 | 256Mi / 250m CPU |
| `prediction-worker` | Deployment | 1-2 | 1Gi / 1000m CPU |
| `notification-worker` | Deployment | 2 | 256Mi / 250m CPU |
| `celery-beat` | Deployment | 1 (singleton) | 128Mi / 100m CPU |
| `postgres` | StatefulSet | 1 (+ replica) | 2Gi / 1000m CPU |
| `redis` | StatefulSet | 3 (Sentinel) | 512Mi / 250m CPU |

## HPA — Auto-scaling API

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: websocket_connections_active
        target:
          type: AverageValue
          averageValue: "50"
```

## Secrets & ConfigMaps

```yaml
# secrets (via External Secrets Operator)
apiVersion: v1
kind: Secret
metadata:
  name: dtf-secrets
type: Opaque
data:
  JWT_SECRET_KEY: <base64>
  DATABASE_PASSWORD: <base64>
  SMTP_PASSWORD: <base64>

# configmap
apiVersion: v1
kind: ConfigMap
metadata:
  name: dtf-config
data:
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "15"
```

## Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Network Policies

- API pods : ingress from Ingress controller only
- Worker pods : no ingress, egress to postgres + redis only
- Postgres : ingress from API + workers only
- Redis : ingress from API + workers only

## GitOps (futur)

| Outil | Usage |
|-------|-------|
| ArgoCD | GitOps deployments |
| Helm | Chart packaging |
| External Secrets | Secret management |
| cert-manager | TLS certificates |

## Migration path

| Phase | Infrastructure |
|-------|----------------|
| Phase 1 | Docker Compose local |
| Phase 2 | Single VPS + Docker Compose |
| Phase 3 | Kubernetes (managed: EKS/GKE/AKS) |
| Phase 4 | Multi-region + Redis Cluster |

## Estimation coûts (production légère)

| Service | Spec | Coût/mois estimé |
|---------|------|-----------------|
| K8s cluster (3 nodes) | t3.medium | ~$90 |
| PostgreSQL (managed) | db.t3.small | ~$25 |
| Redis (managed) | cache.t3.micro | ~$15 |
| Load Balancer | — | ~$20 |
| **Total** | | **~$130/mois** |
