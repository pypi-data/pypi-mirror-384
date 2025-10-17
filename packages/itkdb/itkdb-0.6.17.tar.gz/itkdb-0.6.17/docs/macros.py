# this file is run via gen-files
# https://github.com/facelessuser/pymdown-extensions/issues/933
from __future__ import annotations

import pymdownx.magiclink

base_url = "https://gitlab.cern.ch"
pymdownx.magiclink.PROVIDER_INFO["gitlab"].update(
    {
        "url": base_url,
        "issue": f"{base_url}/{{}}/{{}}/issues/{{}}",
        "pull": f"{base_url}/{{}}/{{}}/merge_requests/{{}}",
        "commit": f"{base_url}/{{}}/{{}}/commit/{{}}",
        "compare": "{base_url}/{{}}/{{}}/compare/{{}}...{{}}",
    }
)
