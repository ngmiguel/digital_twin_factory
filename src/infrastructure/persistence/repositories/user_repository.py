"""User repository."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.identity.user import User
from src.infrastructure.persistence.models.identity import RoleModel, UserModel, user_roles


class UserRepository:
    """Persistence adapter for User aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel)
            .options(selectinload(UserModel.roles).selectinload(RoleModel.permissions))
            .where(UserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel)
            .options(selectinload(UserModel.roles).selectinload(RoleModel.permissions))
            .where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def email_exists(self, email: str) -> bool:
        result = await self._session.execute(
            select(UserModel.id).where(UserModel.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def add(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            password_hash=user.password_hash,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return user

    async def update(self, user: User) -> User:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user.id))
        model = result.scalar_one()
        model.last_login = user.last_login
        model.updated_at = user.updated_at
        await self._session.flush()
        return user

    async def assign_role(self, user_id: UUID, role_name: str) -> None:
        user_result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = user_result.scalar_one()
        role_result = await self._session.execute(select(RoleModel).where(RoleModel.name == role_name))
        role_model = role_result.scalar_one()
        await self._session.execute(
            insert(user_roles).values(
                user_id=user_id,
                role_id=role_model.id,
                assigned_at=datetime.now(UTC),
            )
        )
        await self._session.flush()

    async def get_roles_and_permissions(self, user_id: UUID) -> tuple[list[str], list[str]]:
        result = await self._session.execute(
            select(UserModel)
            .options(selectinload(UserModel.roles).selectinload(RoleModel.permissions))
            .where(UserModel.id == user_id)
        )
        model = result.scalar_one()
        roles = [role.name for role in model.roles]
        permissions = sorted({perm.name for role in model.roles for perm in role.permissions})
        return roles, permissions

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            tenant_id=model.tenant_id,
            email=model.email,
            password_hash=model.password_hash,
            first_name=model.first_name,
            last_name=model.last_name,
            is_active=model.is_active,
            last_login=model.last_login,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
