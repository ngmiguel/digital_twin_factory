# Git Workflow — Digital Twin Factory

## Branches

| Branche | Rôle |
|---------|------|
| `main` | Production stable — releases portfolio |
| `develop` | Intégration continue — merge des features |
| `feat/*` | Branches de fonctionnalités |

## Flux

```
feat/auth          → merge → develop
feat/factory-*     → merge → develop
feat/simulation-*  → merge → develop
develop            → merge → main (release)
```

## Commandes

```powershell
# Nouvelle feature
git checkout develop
git pull origin develop
git checkout -b feat/nom-feature

# Après commits
git push -u origin feat/nom-feature

# Merge dans develop
git checkout develop
git merge --no-ff feat/nom-feature -m "merge: description"
git push origin develop

# Release vers main
git checkout main
git merge --no-ff develop -m "release: v0.x.x"
git push origin main
```
