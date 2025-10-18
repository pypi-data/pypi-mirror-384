from litestar import Router
from litestar import get
from litestar.controller import Controller
from msgspec import Struct
from advanced_alchemy.extensions.litestar.providers import create_service_dependencies
from .models import UserModel
from .services import AuthService
from typing import Annotated
from advanced_alchemy.filters import FilterTypes
from litestar.params import Dependency
from advanced_alchemy.service import OffsetPagination
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig


class User(Struct):
    name: str


class UserDTO(SQLAlchemyDTO[UserModel]):
    config = SQLAlchemyDTOConfig()


class UserController(Controller):
    dependencies = create_service_dependencies(
        AuthService,
        key="auth_service",
        filters={
            "created_at": True,
            "updated_at": True,
            "sort_field": "email",
            "search": "email",
        },
    )
    return_dto = UserDTO

    @get(operation_id="ListUsers", path="/users")
    async def list_tags(
        self,
        auth_service: AuthService,
        filters: Annotated[list[FilterTypes], Dependency(skip_validation=True)],
    ) -> OffsetPagination[UserModel]:
        """List tags."""
        results, total = await auth_service.list_and_count(*filters)
        return auth_service.to_schema(data=results, total=total, filters=filters)


auth_router = Router(
    path="/api/auth",
    route_handlers=[UserController],
)
