from .plugin import AuthPlugin
from .api import auth_router


def init_app(services, session_maker=None):
    services.handlers.append(auth_router)
    services.plugins.append(AuthPlugin(session_maker))
