"""Spec schema, guardrails, and the tool definition the LLM is allowed to call."""
import re

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{2,30}$")

# Add gcp / azure / oci entries here as you add modules.
GUARDRAILS = {
    "aws": {
        "regions": ["us-east-1", "us-east-2", "us-west-2", "eu-west-1"],
        "vm_sizes": {"small": "t3.micro", "medium": "t3.small", "large": "t3.medium"},
    },
}
RESOURCE_TYPES = ["vm", "storage"]

TOOLS = [
    {
        "name": "create_resources",
        "description": (
            "Add cloud resources to the project and generate a Terraform plan. "
            "This NEVER applies changes; the human approves apply separately."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cloud": {"type": "string", "enum": list(GUARDRAILS)},
                "region": {"type": "string"},
                "resources": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": RESOURCE_TYPES},
                            "name": {"type": "string", "description": "lowercase, digits, hyphens, 3-31 chars"},
                            "size": {"type": "string", "enum": ["small", "medium", "large"],
                                     "description": "VMs only"},
                        },
                        "required": ["type", "name"],
                    },
                },
            },
            "required": ["cloud", "region", "resources"],
        },
    }
]

SYSTEM_PROMPT = """You help users provision cloud infrastructure via Terraform.
Supported clouds: aws (more coming). Supported resources: vm, storage.
When the user's request is clear, call create_resources. If cloud, region, or names are
missing, ask briefly. You cannot apply changes: after a plan is produced, tell the user to
review it and type /apply. Never ask for or repeat credentials."""


def validate(req: dict, existing: list[dict]) -> list[str]:
    errors = []
    g = GUARDRAILS.get(req.get("cloud"))
    if not g:
        return [f"Unsupported cloud: {req.get('cloud')}"]
    if req.get("region") not in g["regions"]:
        errors.append(f"Region not allowed. Choose from {g['regions']}")
    names = {r["name"] for r in existing}
    for r in req.get("resources", []):
        if r.get("type") not in RESOURCE_TYPES:
            errors.append(f"Unknown type: {r.get('type')}")
        if not NAME_RE.match(r.get("name", "")):
            errors.append(f"Bad name '{r.get('name')}' (use lowercase letters, digits, hyphens; 3-31 chars)")
        if r.get("name") in names:
            errors.append(f"Name already used: {r.get('name')}")
        names.add(r.get("name"))
        if r.get("type") == "vm" and r.get("size", "small") not in g["vm_sizes"]:
            errors.append(f"Bad VM size: {r.get('size')}")
    return errors
