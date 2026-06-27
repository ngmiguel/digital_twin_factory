# Redis Strategy — Digital Twin Factory

## Instances Redis

| DB Index | Usage | Persistence |
|----------|-------|-------------|
| 0 | Pub/Sub channels (temps réel) | Non |
| 1 | Cache (latest metrics, sessions) | RDB snapshot |
| 2 | Celery broker | AOF |
| 3 | Celery results backend | TTL auto |
| 4 | Rate limiting | TTL auto |

## Clés et TTL

### Cache — Métriques live

| Clé | Type | TTL | Description |
|-----|------|-----|-------------|
| `tenant:{tid}:machine:{mid}:latest` | HASH | 60s | Dernière métrique machine |
| `tenant:{tid}:factory:{fid}:summary` | HASH | 30s | Résumé usine (counts, alerts) |
| `tenant:{tid}:machines:status` | HASH | 60s | Status toutes machines |

### Sessions — Refresh tokens

| Clé | Type | TTL | Description |
|-----|------|-----|-------------|
| `refresh:{jti}` | STRING | 7j | Refresh token actif |
| `user:{uid}:sessions` | SET | 7j | Liste jti actifs |
| `blacklist:{jti}` | STRING | 15min | Access token révoqué |

### Rate Limiting

| Clé | Type | TTL | Limite |
|-----|------|-----|--------|
| `ratelimit:login:{ip}` | STRING | 1min | 5 req/min |
| `ratelimit:api:{uid}` | STRING | 1min | 1000 req/min |
| `ratelimit:export:{uid}` | STRING | 1h | 10 req/h |
| `ratelimit:ws:{ip}` | STRING | 1min | 10 conn/min |

### What-if Scenarios

| Clé | Type | TTL | Description |
|-----|------|-----|-------------|
| `whatif:{scenario_id}` | HASH | 1h | Résultat simulation what-if |

### Pub/Sub Channels

| Channel | Publisher | Subscribers |
|---------|-----------|-------------|
| `tenant:{tid}:factory:{fid}:metrics` | Simulation | WebSocket API |
| `tenant:{tid}:factory:{fid}:alerts` | Monitoring | WebSocket API, Notification |
| `tenant:{tid}:machine:{mid}:status` | Simulation | Monitoring |
| `tenant:{tid}:events` | All services | Audit (futur) |

## Patterns d'utilisation

### Write-through cache (métriques)

```
Simulation tick
  → INSERT PostgreSQL (batch async)
  → SET Redis latest metric (TTL 60s)
  → PUBLISH Redis channel
```

### Cache-aside (lecture API)

```
GET /machines/{id}/metrics/latest
  → GET Redis key
  → Si absent : SELECT PostgreSQL LIMIT 1
  → SET Redis + return
```

### Distributed lock (Celery)

```
simulate_machine_tick
  → SET lock:machine:{mid} NX EX 5
  → Si lock acquired : simulate
  → DEL lock
```

## Configuration production

```yaml
# redis.conf recommandé
maxmemory: 512mb
maxmemory-policy: allkeys-lru
save: "900 1 300 10 60 10000"
appendonly: yes
appendfsync: everysec
```

## Monitoring Redis

| Métrique | Alerte si |
|----------|-----------|
| `used_memory` | > 80% maxmemory |
| `connected_clients` | > 500 |
| `pubsub_channels` | > 1000 |
| `keyspace_misses` ratio | > 30% |

## Évolution Phase 3

- Redis Sentinel pour HA
- Redis Cluster si > 10 tenants actifs
- Migration Pub/Sub → Redis Streams pour replay
