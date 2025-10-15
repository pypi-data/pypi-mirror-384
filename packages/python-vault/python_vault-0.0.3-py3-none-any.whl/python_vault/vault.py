import os

import hvac
from custom_python_logger import get_logger


class VaultClient:
    def __init__(
        self, vault_addr: str = None, vault_role_id: str = None, vault_secret_id: str = None, vault_mount: str = None
    ) -> None:
        self.logger = get_logger(self.__class__.__name__)

        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self.vault_role_id = vault_role_id or os.getenv("VAULT_ROLE_ID")
        self.vault_secret_id = vault_secret_id or os.getenv("VAULT_SECRET_ID")
        self.vault_mount = vault_mount or os.getenv("VAULT_MOUNT")

        self.client = hvac.Client(url=self.vault_addr)
        self._authenticate()

    def _authenticate(self) -> None:
        self.client.auth.approle.login(role_id=self.vault_role_id, secret_id=self.vault_secret_id)
        if not self.client.is_authenticated():
            raise Exception("Vault AppRole authentication failed")

    def read_secret(self, path: str) -> dict:
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path, mount_point=self.vault_mount, raise_on_deleted_version=True
        )
        return response
