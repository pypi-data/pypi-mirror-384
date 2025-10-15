# Python Vault Client

A lightweight Python wrapper for **HashiCorp Vault** using the `hvac` library.
This utility class enables secure and simple authentication via **AppRole**, and allows easy retrieval of secrets from Vault using the **KV v2 engine**.

---

## Features

* ✅ Simple AppRole-based authentication using role ID and secret ID
* ✅ Automatic environment variable support (`VAULT_ADDR`, `VAULT_ROLE_ID`, etc.)
* ✅ Built-in validation for successful authentication
* ✅ Easy integration into other Python projects or CI pipelines
* ✅ Read secrets directly from Vault’s KV v2 engine
* ✅ Configurable mount point and secret path

---

## Installation
```bash
pip install python-vault
```

---

### 🔧 Configuration

Environment variables used by default (can be overridden via constructor):

* `VAULT_ADDR`: Vault URL
* `VAULT_ROLE_ID`: AppRole role ID
* `VAULT_SECRET_ID`: AppRole secret ID
* `VAULT_MOUNT`: Vault KV engine mount path

---

### 📦 Example Usage

```python
import json
from python_vault import VaultClient

vault = VaultClient()
secret_data = vault.read_secret("path/to/secret")
print(json.dumps(secret_data, indent=4))
```

You can also pass configuration explicitly:

```python
import json
from python_vault import VaultClient

vault = VaultClient(
    vault_addr="https://vault.mycompany.com",
    vault_role_id="your-role-id",
    vault_secret_id="your-secret-id",
    vault_mount="kv"
)
secret_data = vault.read_secret("path/to/secret")
print(json.dumps(secret_data, indent=4))
```

---

## 🤝 Contributing
If you have a helpful tool, pattern, or improvement to suggest:
Fork the repo <br>
Create a new branch <br>
Submit a pull request <br>
I welcome additions that promote clean, productive, and maintainable development. <br>

---

## 🙏 Thanks
Thanks for exploring this repository! <br>
Happy coding! <br>
