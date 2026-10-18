"""Holds desired state (spec.json) and renders it to Terraform JSON."""
import json
from pathlib import Path

from spec import GUARDRAILS

ROOT = Path(__file__).parent.resolve()
MODULES = ROOT / "modules"


class Project:
    def __init__(self, name: str):
        self.dir = ROOT / "workspaces" / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.dir / "spec.json"
        self.spec = {"cloud": None, "region": None, "resources": []}
        if self.state_file.exists():
            self.spec = json.loads(self.state_file.read_text())

    def add(self, req: dict) -> str | None:
        """Merge a validated request. Returns an error string or None."""
        s = self.spec
        if s["cloud"] and (s["cloud"], s["region"]) != (req["cloud"], req["region"]):
            return (f"This project is pinned to {s['cloud']}/{s['region']}. "
                    "Use a new project for another cloud or region.")
        s["cloud"], s["region"] = req["cloud"], req["region"]
        for r in req["resources"]:
            s["resources"].append({"type": r["type"], "name": r["name"], "size": r.get("size", "small")})
        self.state_file.write_text(json.dumps(s, indent=2))
        return None

    def render(self) -> None:
        s = self.spec
        cloud = s["cloud"]
        g = GUARDRAILS[cloud]
        tf = {
            "terraform": {"required_providers": {
                "aws": {"source": "hashicorp/aws", "version": "~> 5.0"},
                "random": {"source": "hashicorp/random", "version": "~> 3.6"},
            }},
            "provider": {"aws": {
                "region": s["region"],
                "default_tags": {"tags": {"ManagedBy": "cloudbot", "Project": self.dir.name}},
            }},
            "module": {},
            "output": {},
        }
        for r in s["resources"]:
            src = str(MODULES / cloud / r["type"])
            if r["type"] == "vm":
                tf["module"][r["name"]] = {"source": src, "name": r["name"],
                                           "instance_type": g["vm_sizes"][r["size"]]}
                for out in ("instance_id", "public_ip"):
                    tf["output"][f"{r['name']}_{out}"] = {"value": f"${{module.{r['name']}.{out}}}"}
            elif r["type"] == "storage":
                tf["module"][r["name"]] = {"source": src, "name": r["name"]}
                tf["output"][f"{r['name']}_bucket"] = {"value": f"${{module.{r['name']}.bucket_name}}"}
        (self.dir / "main.tf.json").write_text(json.dumps(tf, indent=2))

    def summary(self) -> str:
        if not self.spec["resources"]:
            return "No resources yet."
        lines = [f"{self.spec['cloud']}/{self.spec['region']}"]
        lines += [f"- {r['type']}: {r['name']}" + (f" ({r['size']})" if r["type"] == "vm" else "")
                  for r in self.spec["resources"]]
        return "\n".join(lines)
