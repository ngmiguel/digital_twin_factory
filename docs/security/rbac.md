# RBAC — Role-Based Access Control

## Modèle de permissions

Format : `{resource}:{action}`

| Resource | Actions |
|----------|---------|
| `factory` | read, write, delete |
| `machine` | read, write, delete, start, stop |
| `metric` | read, export |
| `alert` | read, write |
| `prediction` | read |
| `maintenance` | read, write |
| `simulation` | read, write |
| `user` | read, write, delete |
| `role` | read, write |
| `tenant` | read, write |
| `notification` | read, write |

## Rôles système

### `super_admin`
Permissions : `*` (toutes)
Scope : Plateforme entière, tous tenants

### `tenant_admin`
| Permission | Description |
|------------|-------------|
| `factory:*` | Gestion complète usines |
| `machine:*` | Gestion complète machines |
| `user:*` | Gestion utilisateurs tenant |
| `role:read` | Voir les rôles |
| `metric:*` | Métriques + export |
| `alert:*` | Alertes complètes |
| `prediction:read` | Voir prédictions |
| `maintenance:*` | Maintenance complète |
| `simulation:*` | Simulation + what-if |
| `notification:*` | Notifications |
| `tenant:read` | Voir config tenant |

### `operator`
| Permission | Description |
|------------|-------------|
| `factory:read` | Voir usines |
| `machine:read` | Voir machines |
| `metric:read` | Dashboard live |
| `alert:read` | Voir alertes |
| `alert:write` | Acquitter alertes |
| `notification:read` | Voir notifications |

### `maintenance_engineer`
| Permission | Description |
|------------|-------------|
| `factory:read` | Voir usines |
| `machine:read` | Voir machines |
| `metric:read` | Métriques |
| `metric:export` | Export données |
| `alert:*` | Alertes complètes |
| `prediction:read` | Prédictions |
| `maintenance:*` | Maintenance complète |
| `simulation:write` | What-if scenarios |
| `notification:read` | Notifications |

### `viewer`
| Permission | Description |
|------------|-------------|
| `factory:read` | Voir usines |
| `machine:read` | Voir machines |
| `metric:read` | Métriques |
| `alert:read` | Alertes (lecture seule) |

## Matrice complète

| Permission | super_admin | tenant_admin | operator | maint_eng | viewer |
|------------|:-----------:|:------------:|:--------:|:---------:|:------:|
| factory:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| factory:write | ✓ | ✓ | ✗ | ✗ | ✗ |
| factory:delete | ✓ | ✓ | ✗ | ✗ | ✗ |
| machine:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| machine:write | ✓ | ✓ | ✗ | ✗ | ✗ |
| machine:start | ✓ | ✓ | ✗ | ✗ | ✗ |
| metric:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| metric:export | ✓ | ✓ | ✗ | ✓ | ✗ |
| alert:read | ✓ | ✓ | ✓ | ✓ | ✓ |
| alert:write | ✓ | ✓ | ✓ | ✓ | ✗ |
| prediction:read | ✓ | ✓ | ✗ | ✓ | ✗ |
| maintenance:read | ✓ | ✓ | ✗ | ✓ | ✗ |
| maintenance:write | ✓ | ✓ | ✗ | ✓ | ✗ |
| simulation:write | ✓ | ✓ | ✗ | ✓ | ✗ |
| user:read | ✓ | ✓ | ✗ | ✗ | ✗ |
| user:write | ✓ | ✓ | ✗ | ✗ | ✗ |
| tenant:read | ✓ | ✓ | ✗ | ✗ | ✗ |
| tenant:write | ✓ | ✗ | ✗ | ✗ | ✗ |

## Implémentation

### Vérification dans FastAPI

```python
# Conceptuel — pas de code implémenté encore
@router.post("/factories")
@require_permission("factory:write")
async def create_factory(command: CreateFactoryCommand, user: CurrentUser):
    ...
```

### Permissions dans JWT

Les permissions sont incluses dans l'access token pour éviter une DB lookup à chaque requête. Recalculées à chaque refresh token (max 15 min de délai si permissions changent).

### Custom roles (futur)

Les `tenant_admin` pouront créer des rôles custom avec un sous-set de permissions.

## Seed data (rôles et permissions initiaux)

Migration Alembic `seed_rbac` insère :
- 5 rôles système
- 20 permissions
- Associations role_permissions selon matrice ci-dessus
