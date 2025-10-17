

# common/authz_utils/decorators.py

from functools import wraps
from flask import current_app, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError
import traceback
from solving_auth_middleware.enums import UserTypeEnum
from flask_restx import abort

def requires_permissions(
    expected_user_types: list[UserTypeEnum],
    resource_loader=None,
    remote_check_func=None,
    required_permissions: list[str] = None,
    permissions_check_func=None,
    location: str = 'headers',
    fresh: bool = False
):
    """
    expected_user_types : ex. [UserTypeEnum.PRO]
    resource_loader : fonction -> ressource métier (ex: Patient)
    remote_check_func : fonction (jwt, resource) → bool
    required_permissions : liste de permissions présentes dans le JWT (ex: ['can_view'])
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required(locations=[location], fresh=fresh)
        def wrapper(*args, **kwargs):
            try:
                jwt = get_jwt()
                user_type = jwt.get("user_type")

                # 1. Vérifier le type d'utilisateur
                if user_type not in [user_type.value for user_type in expected_user_types]:
                    abort(403, "Forbidden: user_type mismatch")

                # 2. Vérifier les permissions
                if required_permissions and permissions_check_func and expected_user_types == [UserTypeEnum.PRO]:
                    if not permissions_check_func(jwt, required_permissions):
                        abort(403, "Forbidden: missing permissions")

                # 3. Charger la ressource métier
                resource = resource_loader(**kwargs) if resource_loader else None

                # 4. Vérification distante
                if remote_check_func and not remote_check_func(jwt, resource):
                    abort(403, "Forbidden: remote check failed")

                # 5. Tout est bon
                return fn(*args, **kwargs)

            except (JWTExtendedException, PyJWTError) as e:
                current_app.logger.error(f"Error in requires_permissions: {e}")
                abort(401, "Authentication error")

        return wrapper
    return decorator


