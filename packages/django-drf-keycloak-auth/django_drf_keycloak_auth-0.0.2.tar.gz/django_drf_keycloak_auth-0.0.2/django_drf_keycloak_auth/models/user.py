from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class User:

    username: str = field(init=False)
    given_name: Optional[str] = field(init=False)
    family_name: Optional[str] = field(init=False)
    preferred_username: Optional[str] = field(init=False)
    email: Optional[str] = field(init=False)
    email_verified: bool = field(init=False, default=False)
    sub: str = field(init=False)
    claims: dict = field(default_factory=dict)
    roles: List[str] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.username = (
            self.claims.get("preferred_username")
            or self.claims.get("email")
            or self.claims.get("sub")
        )
        self.given_name = self.claims.get("given_name")
        self.family_name = self.claims.get("family_name")
        self.preferred_username = self.claims.get("preferred_username")
        self.email = self.claims.get("email")
        self.email_verified = self.claims.get("email_verified")
        self.sub = self.claims.get("sub")
        self.roles = self.__extract_roles_from_claims()

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_username(self) -> str:
        return self.username

    @property
    def pk(self):
        return self.username

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, roles: Iterable[str]) -> bool:
        return any(self.has_role(role) for role in roles)

    def has_all_roles(self, roles: Iterable[str]) -> bool:
        return all(self.has_role(role) for role in roles)

    def __extract_roles_from_claims(self) -> List[str]:
        """
        Extract roles from Keycloak userinfo/claims (first realm access, then merge the client roles of resource access).
        Return a list of de-duplicated role strings (such as ['admin', 'user', 'clientA:roleX']).
        """
        roles = set()

        # realm roles: {"realm_access": {"roles": ["role1", ...]}}
        realm_access = self.claims.get("realm_access", {}) or {}
        for r in realm_access.get("roles", []) or []:
            roles.add(r)

        # client/resource roles: {"resource_access": {"client-id": {"roles":["r1",...]}, ...}}
        resource_access = self.claims.get("resource_access", {}) or {}
        for client, info in (
            resource_access.items() if isinstance(resource_access, dict) else []
        ):
            client_roles = info.get("roles", []) if isinstance(info, dict) else []
            for cr in client_roles or []:
                # To avoid naming conflicts, use the form "client:role"
                roles.add(f"{client}:{cr}")

        return sorted(roles)

    def to_dict(self):
        return {
            "username": self.username,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "preferred_username": self.preferred_username,
            "email": self.email,
            "email_verified": self.email_verified,
            "sub": self.sub,
            "claims": self.claims,
            "roles": self.roles,
        }
