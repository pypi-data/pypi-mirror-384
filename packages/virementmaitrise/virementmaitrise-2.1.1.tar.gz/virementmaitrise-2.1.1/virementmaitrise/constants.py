# -*- coding: utf-8 -*-

# Model types for AIS authentication
DECOUPLED_MODEL_TYPE = "decoupled"
REDIRECT_MODEL_TYPE = "redirect"

# Headers for signature verification
SIGNED_HEADER_PARAMETER_LIST = [
    "(request-target)",
    "Date",
    "Digest",
    "X-Request-ID",
]

# API base URLs - tenant specific
PRODUCTION_API_BASE = "https://api.virementmaitrise.societegenerale.eu"
SANDBOX_API_BASE = "https://api.sandbox.virementmaitrise.societegenerale.eu"
