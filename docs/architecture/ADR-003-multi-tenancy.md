# ADR-003 — Multi-Tenancy Strategy

**Statut :** Accepté  
**Date :** 2025-06-27

## Contexte

La plateforme doit supporter plusieurs organisations (tenants) isolées : une usine d'un client ne doit jamais être visible par un autre.

## Décision

**Shared Database, Shared Schema** avec colonne `tenant_id` sur toutes les tables métier + **Row Level Security (RLS)** PostgreSQL.

### Implémentation

1. Chaque requête SQL inclut `WHERE tenant_id = :current_tenant_id`
2. RLS PostgreSQL comme filet de sécurité :
   ```sql
   CREATE POLICY tenant_isolation ON factories
       USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
   ```
3. Le middleware FastAPI extrait `tenant_id` du JWT et set la variable de session PostgreSQL
4. Le slug tenant est utilisé pour les URLs publiques : `/api/v1/t/{slug}/factories`

### Isolation des données Redis

Préfixe `tenant:{tenant_id}:` sur toutes les clés Redis.

### Isolation Celery

Chaque task Celery reçoit `tenant_id` en paramètre — jamais inféré globalement.

## Conséquences

- Simple à opérer (un seul DB)
- RLS protège contre les bugs d'application
- Migration vers schema-per-tenant possible si un client enterprise l'exige

## Alternatives rejetées

| Alternative | Raison |
|-------------|--------|
| Database per tenant | Coût opérationnel élevé |
| Schema per tenant | Complexité migrations Alembic |
