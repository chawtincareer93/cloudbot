# cloudbot

Chat -> structured spec -> Terraform JSON -> plan -> human approves apply.

## Setup
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...
    export AWS_PROFILE=...        # or AWS_ACCESS_KEY_ID / SECRET (least privilege)
    python bot.py my-project

Needs `terraform` on PATH. Try: "a small VM and a bucket called demo-logs in us-east-1".
Commands: /list  /apply  /destroy  /quit

## Layout
- spec.py     schema, guardrails, the single LLM tool
- project.py  desired state (spec.json) + renders main.tf.json
- tf.py       terraform subprocess wrapper
- bot.py      chat loop; apply/destroy are human-only
- modules/<cloud>/<type>/   one folder per cloud + resource

## Adding a cloud
1. Add an entry to GUARDRAILS in spec.py (regions, vm_sizes).
2. Create modules/<cloud>/vm and /storage with the same variables/outputs as AWS.
3. In project.py, add the provider block and per-cloud branch in render().

## Next steps
- Remote backend (S3/GCS/Blob/OCI) instead of local state
- Infracost in the plan step
- Per-user projects and credentials
