# Poelis Python SDK

Python SDK for Poelis.

## Installation

```bash
pip install -U poelis-sdk
```

Requires Python 3.11+.

## Quickstart (API key + org ID)

```python
from poelis_sdk import PoelisClient

client = PoelisClient(
    api_key="poelis_live_A1B2C3...",    # Organization Settings → API Keys
    org_id="tenant_uci_001",            # same section
)
```

## Configuration

### Getting your API key and org ID

1. Navigate to Organization Settings → API Keys.
2. Click “Create API key”, choose a name and scopes (read-only by default recommended).
3. Copy the full key when shown (it will be visible only once). Keep it secret.
4. The `org_id` for your organization is displayed in the same section.
5. You can rotate or revoke keys anytime. Prefer storing as env vars:

```bash
export POELIS_API_KEY=poelis_live_A1B2C3...
export POELIS_ORG_ID=tenant_id_001
```


### How authentication works

The SDK does not talk to Auth0. It sends your API key directly to the Poelis backend for validation on every request.

- Default headers sent by the SDK:

  - `X-API-Key: <api_key>` (and `X-Poelis-Api-Key` as a compatibility alias)
  - `Authorization: Api-Key <api_key>` (compatibility for gateways expecting Authorization-only)
  - `X-Poelis-Org: <org_id>`

You can opt into Bearer mode (legacy) by setting `POELIS_AUTH_MODE=bearer`, which will send:

  - `Authorization: Bearer <api_key>`
  - `X-Poelis-Org: <org_id>`

The backend validates the API key against your organization, applies authorization and filtering, and returns data.


## Dot-path browser (Notebook UX)

The SDK exposes a dot-path browser for easy exploration:

```python
client.browser  # then use TAB to explore
# client.browser.<workspace>.<product>.<item>.<child>.properties
```

See the example notebook in `notebooks/try_poelis_sdk.ipynb` for an end-to-end walkthrough (authentication, listing workspaces/products/items, and simple search queries). The client defaults to `https://api.poelis.ai` unless `POELIS_BASE_URL` is set.

## Requirements

- Python >= 3.11
- API base URL reachable from your environment

## License

MIT
