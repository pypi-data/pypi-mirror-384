# authflow - Backend Package

Python/FastAPI backend for authflow-stack.

## Installation

```bash
pip install authflow
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from authflow import AuthFlow, setup_auth
from authflow.dependencies import get_current_user, require_permission

app = FastAPI()

# Initialize from config file
auth = AuthFlow.from_config("authflow.config.yaml")
setup_auth(app, auth, prefix="/api/v1/auth")

# Protected route
@app.get("/api/data")
async def get_data(user = Depends(get_current_user)):
    return {"message": f"Hello {user.username}"}

# Permission-protected route
@app.post("/api/contracts")
@require_permission("contracts:write")
async def create_contract(user = Depends(get_current_user)):
    return {"status": "created"}
```

## Configuration

Create `authflow.config.yaml`:

```yaml
provider:
  type: keycloak
  keycloak:
    url: https://keycloak.example.com
    realm: my-realm
    client_id: authflow-client
    client_secret: ${KEYCLOAK_SECRET}

features:
  organizations: true
  teams: true
  email_verification: true

rbac:
  model: role-based
  scopes: [global, organization, team]
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
