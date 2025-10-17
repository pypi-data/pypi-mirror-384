class BasePermission:
    """
    Interface for any permission checker.
    """
    def __init__(self, claims: dict, permission: str = None, value=None, **kwargs):
        self.user = claims
        self.permission = permission
        self.value = value
        self.extras = kwargs

    def has_access(self) -> bool:
        raise NotImplementedError
    

class Permission(BasePermission):
    """
    Default permission checker for claims stored in nested JSON.
    """

    def __init__(self, claims: dict, permission: str = None, value=None):
        super().__init__(claims, permission, value)

    def has_access(self) -> bool:
        if not self.permission:
            return True 

        keys = self.permission.split(".")
        node = self.user.get('permissions', {})

        try:
            for key in keys:
                if isinstance(node, dict):
                    node = node.get(key)
                else:
                    return False
        except Exception:
            return False

        if node == "*":
            return True 
    
        if node is None:
            return False

        if isinstance(self.value, list) and  not isinstance(node, (dict,list)):
                    return node in self.value
        
        if isinstance(node, list):
            if self.value is not None:
                if isinstance(self.value, list):
                    return any(v in node for v in self.value)
                
                return self.value in node
            return False

        # Primitive value comparison or truthy check if no value provided
        return node == self.value if self.value is not None else bool(node)

        