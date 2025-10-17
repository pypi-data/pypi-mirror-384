"""
Système de validation d'accès modulaire pour le middleware d'authentification.

Ce module fournit des validators (validateurs) qui peuvent être combinés pour créer
des règles de validation d'accès flexibles et réutilisables.
"""

from typing import Callable, List, Optional, Any, Dict
from abc import ABC, abstractmethod
from flask import current_app, request
import requests
from solving_auth_middleware.enums import UserTypeEnum


class AccessValidator(ABC):
    """Classe de base abstraite pour tous les validators d'accès."""
    
    @abstractmethod
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        """
        Valide l'accès selon les critères du validator.
        
        Args:
            jwt_data: Les données décodées du JWT
            identity: L'identité de l'utilisateur (depuis get_jwt_identity())
            token: Le token JWT complet
            **context: Contexte additionnel (ressource, kwargs, etc.)
            
        Returns:
            tuple: (succès: bool, message_erreur: Optional[str])
        """
        pass


class UserTypeValidator(AccessValidator):
    """Valide que l'utilisateur appartient à un ou plusieurs types autorisés."""
    
    def __init__(self, allowed_types: List[UserTypeEnum]):
        """
        Args:
            allowed_types: Liste des types d'utilisateurs autorisés
        """
        self.allowed_types = allowed_types
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        user_type = jwt_data.get("user_type")
        
        if user_type in [ut.value for ut in self.allowed_types]:
            return True, None
        
        return False, f"Type d'utilisateur non autorisé. Requis: {[ut.value for ut in self.allowed_types]}, Actuel: {user_type}"


class PermissionsValidator(AccessValidator):
    """Valide que l'utilisateur possède les permissions requises."""
    
    def __init__(self, required_permissions: List[str], mode: str = "all"):
        """
        Args:
            required_permissions: Liste des permissions requises
            mode: "all" (toutes les permissions requises) ou "any" (au moins une permission)
        """
        self.required_permissions = required_permissions
        self.mode = mode
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        user_permissions = jwt_data.get("permissions", [])
        
        if self.mode == "all":
            missing = [p for p in self.required_permissions if p not in user_permissions]
            if missing:
                return False, f"Permissions manquantes: {missing}"
        elif self.mode == "any":
            if not any(p in user_permissions for p in self.required_permissions):
                return False, f"Aucune des permissions requises trouvée: {self.required_permissions}"
        
        return True, None


class CustomFunctionValidator(AccessValidator):
    """Valide l'accès via une fonction personnalisée."""
    
    def __init__(self, validation_fn: Callable):
        """
        Args:
            validation_fn: Fonction de validation (jwt_data, identity, token, **context) -> bool
        """
        self.validation_fn = validation_fn
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        try:
            is_valid = self.validation_fn(jwt_data, identity, token, **context)
            if is_valid:
                return True, None
            return False, "Validation personnalisée échouée"
        except Exception as e:
            return False, f"Erreur dans la validation personnalisée: {str(e)}"


class RemoteAPIValidator(AccessValidator):
    """Valide l'accès via un appel à une API distante."""
    
    def __init__(self, endpoint: str, timeout: int = 10):
        """
        Args:
            endpoint: URL de l'API de validation
            timeout: Timeout en secondes pour l'appel API
        """
        self.endpoint = endpoint
        self.timeout = timeout
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        try:
            response = requests.post(
                self.endpoint,
                json={
                    'identity': identity,
                    'jwt_data': jwt_data,
                    'context': context
                },
                headers={'Authorization': f'Bearer {token}'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return True, None
            
            error_msg = response.json().get('message', 'Validation distante échouée')
            return False, error_msg
            
        except requests.RequestException as e:
            return False, f"Erreur lors de l'appel à l'API de validation: {str(e)}"


class ResourceOwnerValidator(AccessValidator):
    """Valide que l'utilisateur est propriétaire de la ressource."""
    
    def __init__(self, resource_loader: Callable, owner_field: str = "owner_id"):
        """
        Args:
            resource_loader: Fonction qui charge la ressource (utilise **kwargs)
            owner_field: Champ dans la ressource qui contient l'ID du propriétaire
        """
        self.resource_loader = resource_loader
        self.owner_field = owner_field
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        try:
            kwargs = context.get('kwargs', {})
            resource = self.resource_loader(**kwargs)
            
            if resource is None:
                return False, "Ressource non trouvée"
            
            # Gestion des objets et des dictionnaires
            if isinstance(resource, dict):
                owner_id = resource.get(self.owner_field)
            else:
                owner_id = getattr(resource, self.owner_field, None)
            
            if str(owner_id) == str(identity):
                return True, None
            
            return False, "Vous n'êtes pas le propriétaire de cette ressource"
            
        except Exception as e:
            return False, f"Erreur lors de la vérification de propriété: {str(e)}"


class ClaimValidator(AccessValidator):
    """Valide la présence et/ou la valeur d'un claim spécifique dans le JWT."""
    
    def __init__(self, claim_name: str, expected_value: Any = None):
        """
        Args:
            claim_name: Nom du claim à vérifier
            expected_value: Valeur attendue (si None, vérifie seulement la présence)
        """
        self.claim_name = claim_name
        self.expected_value = expected_value
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        if self.claim_name not in jwt_data:
            return False, f"Claim manquant: {self.claim_name}"
        
        if self.expected_value is not None:
            actual_value = jwt_data.get(self.claim_name)
            if actual_value != self.expected_value:
                return False, f"Valeur du claim incorrecte. Attendu: {self.expected_value}, Actuel: {actual_value}"
        
        return True, None


class CompositeValidator(AccessValidator):
    """Combine plusieurs validators avec une logique AND ou OR."""
    
    def __init__(self, validators: List[AccessValidator], mode: str = "all"):
        """
        Args:
            validators: Liste de validators à combiner
            mode: "all" (tous doivent passer) ou "any" (au moins un doit passer)
        """
        self.validators = validators
        self.mode = mode
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        errors = []
        
        for validator in self.validators:
            is_valid, error_msg = validator.validate(jwt_data, identity, token, **context)
            
            if self.mode == "all":
                if not is_valid:
                    return False, error_msg
            elif self.mode == "any":
                if is_valid:
                    return True, None
                if error_msg:
                    errors.append(error_msg)
        
        if self.mode == "all":
            return True, None
        else:  # mode == "any"
            return False, f"Aucun validator n'a réussi: {'; '.join(errors)}"


class RoleHierarchyValidator(AccessValidator):
    """Valide l'accès basé sur une hiérarchie de rôles."""
    
    # Hiérarchie par défaut (plus le nombre est élevé, plus le rôle est puissant)
    DEFAULT_HIERARCHY = {
        UserTypeEnum.PUBLIC: 0,
        UserTypeEnum.PRO: 1,
        UserTypeEnum.USER_ADMIN: 2,
        UserTypeEnum.SOFTWARE_ADMIN: 3,
        UserTypeEnum.SYSTEM: 4,
    }
    
    def __init__(self, minimum_role: UserTypeEnum, hierarchy: Dict[UserTypeEnum, int] = None):
        """
        Args:
            minimum_role: Rôle minimum requis
            hierarchy: Dictionnaire personnalisé de hiérarchie (optionnel)
        """
        self.minimum_role = minimum_role
        self.hierarchy = hierarchy or self.DEFAULT_HIERARCHY
    
    def validate(self, jwt_data: dict, identity: str, token: str, **context) -> tuple[bool, Optional[str]]:
        user_type_str = jwt_data.get("user_type")
        
        try:
            user_type = UserTypeEnum(user_type_str)
        except ValueError:
            return False, f"Type d'utilisateur invalide: {user_type_str}"
        
        user_level = self.hierarchy.get(user_type, -1)
        required_level = self.hierarchy.get(self.minimum_role, 999)
        
        if user_level >= required_level:
            return True, None
        
        return False, f"Niveau d'accès insuffisant. Requis: {self.minimum_role.value} ou supérieur"

