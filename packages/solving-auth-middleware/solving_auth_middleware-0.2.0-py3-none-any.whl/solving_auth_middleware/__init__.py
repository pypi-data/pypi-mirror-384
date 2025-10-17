from flask import Flask
from .config import Config
from .middleware import requires_permissions
from .enums import UserTypeEnum
from .middleware_v2 import requires_permissions as requires_permissions_v2
from .middleware_v3 import (
    requires_access,
    requires_permissions_v3,
    quick_user_type_check,
    quick_permissions_check,
    quick_role_hierarchy_check
)
from .validators import (
    AccessValidator,
    UserTypeValidator,
    PermissionsValidator,
    CustomFunctionValidator,
    RemoteAPIValidator,
    ResourceOwnerValidator,
    ClaimValidator,
    CompositeValidator,
    RoleHierarchyValidator
)

__version__ = '0.2.0'

def create_app(config_class=Config):
    """Crée et configure une nouvelle instance de l'application Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)
    return app

__all__ = [
    # App factory
    'create_app',
    
    # Configuration
    'Config',
    
    # Enums
    'UserTypeEnum',
    
    # Middleware versions
    'requires_permissions',           # v1 - Original
    'requires_permissions_v2',        # v2 - Version intermédiaire
    'requires_access',                # v3 - Nouvelle version avec validators
    'requires_permissions_v3',        # v3 - Alias
    
    # Quick helpers v3
    'quick_user_type_check',
    'quick_permissions_check',
    'quick_role_hierarchy_check',
    
    # Validators
    'AccessValidator',
    'UserTypeValidator',
    'PermissionsValidator',
    'CustomFunctionValidator',
    'RemoteAPIValidator',
    'ResourceOwnerValidator',
    'ClaimValidator',
    'CompositeValidator',
    'RoleHierarchyValidator'
]
