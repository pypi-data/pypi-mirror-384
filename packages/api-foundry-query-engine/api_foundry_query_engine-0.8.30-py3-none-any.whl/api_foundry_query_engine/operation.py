from typing import Any, Dict, List, Optional


class Operation:
    """
    Represents an action to be performed on an entity.

    The `Operation` class encapsulates the details required
    to execute an operation on a given entity, including
    query parameters for selecting records, parameters for
    storing or updating values, metadata for operational
    instructions, and roles defining the contexts in which
    the operation can be performed.

    Attributes:
        entity (str): The name of the resource or object being
            targeted (e.g., "User", "Order").
        action (str): The type of action being performed
            (e.g., "create", "read", "update", "delete").
        query_params (dict): Parameters used to filter or select
            the records affected by the operation.
        store_params (dict): Parameters that define the values to
            be stored or updated for the selected records.
        metadata_params (dict): Additional instructions for the
            operation, such as sorting or pagination.
        roles (dict): Defines the roles under which the operation
            is allowed to be performed.
    """

    def __init__(
        self,
        *,
        entity: str,
        action: str,
        query_params: Optional[Dict[str, Any]] = None,
        store_params: Optional[Dict[str, Any]] = None,
        metadata_params: Optional[Dict[str, Any]] = None,
        roles: Optional[List[str]] = None,
        scope: Optional[Dict[str, Any]] = None,
        groups: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        subject: Optional[str] = None,
        claims: Optional[Dict[str, Any]] = None,
    ):
        """
        Initializes the Operation instance.

        Args:
            entity (str): The name of the entity to perform the operation on.
            action (str): The action to perform on the entity.
            query_params (dict, optional): Parameters for selecting
                affected records (default: {}).
            store_params (dict, optional): Parameters defining new or
                updated values (default: {}).
            metadata_params (dict, optional): Metadata for the
                operation, such as sorting or pagination (default: {}).
            roles (dict, optional): Defines the roles allowed to
                perform the operation (default: {}).
        """
        # The target entity for the operation (e.g., "User", "Order").
        self.entity = entity

        # The type of action to perform (e.g., "create",
        # "read", "update", "delete").
        self.action = action

        # Query parameters to filter or identify the affected records.
        self.query_params = query_params or {}

        # Parameters defining the values to be stored or updated
        # for the operation.
        self.store_params = store_params or {}

        # Metadata for operational instructions like sorting,
        # limiting, or offsetting results.
        self.metadata_params = metadata_params or {}

        # Roles defining the context in which the operation is allowed.
        self.scope = scope or {}
        self.roles = roles or []
        self.groups = groups or []
        self.permissions = permissions or []

        self.subject = subject
        # Full set of claims (when available). Used for row-level filters
        # like where: "id = ${claims.sub}".
        self.claims = claims or ({"sub": subject} if subject is not None else {})
