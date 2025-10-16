# Hestia Extend Bibliography

## Install

```bash
pip install hestia-earth-extend-bibliography
```

### Usage

```python
from hestia_earth.extend_bibliography import extend

# nodes is a Dict {nodes: []}
result = extend(
  nodes,
  # pass in the desired crendentials for each API
  mendeley_username=MENDELEY_USERNAME, mendeley_password=MENDELEY_PASSWORD, # enable Mendeley SDK
  mendeley_api_url=MENDELEY_API_URL, # enable Mendeley through API URL (default to using the SDK if not provided)
  wos_api_key=WOS_API_KEY, # enable WoS REST API
  enable_unpaywall=False, # enable Unpaywall as fallback
  enable_crossref=False, # enable CrossRef as last fallback (slower)
)
```
