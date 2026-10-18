"""CLI chat loop. The LLM can only call create_resources (which plans).
Apply and destroy are human-only commands, never LLM tools."""
import json
import os
import sys

import anthropic

import tf
from project import Project
from spec import SYSTEM_PROMPT, TOOLS, validate

MODEL = os.environ.get("CLOUDBOT_MODEL", "claude-sonnet-5-5")
client = anthropic.Anthropic()


def handle_create(project: Project, args: dict) -> str:
    errors = validate(args, project.spec["resources"])
    if errors:
        return "Rejected:\n" + "\n".join(errors)
    err = project.add(args)
    if err:
        return "Rejected: " + err
    project.render()
    for step in (tf.init, tf.validate, tf.plan):
        code, out = step(project.dir)
        if code != 0:
            return f"Terraform {step.__name__} failed:\n{out[-2000:]}"
    # Return only the tail of the plan (resource list + summary) to the model.
    print("\n----- TERRAFORM PLAN -----\n" + out + "\n--------------------------\n")
    return "Plan succeeded. Summary:\n" + out[-1500:]


def chat_turn(project: Project, messages: list) -> None:
    while True:
        resp = client.messages.create(model=MODEL, max_tokens=1500, system=SYSTEM_PROMPT,
                                      tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        for block in resp.content:
            if block.type == "text" and block.text.strip():
                print(f"\nbot> {block.text}\n")
        if resp.stop_reason != "tool_use":
            return
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": handle_create(project, block.input)})
        messages.append({"role": "user", "content": results})


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "default"
    project = Project(name)
    messages: list = []
    print(f"cloudbot project '{name}'. Commands: /apply /destroy /list /quit")
    while True:
        text = input("you> ").strip()
        if not text:
            continue
        if text == "/quit":
            return
        if text == "/list":
            print(project.summary())
        elif text == "/apply":
            if not (project.dir / "tfplan").exists():
                print("No plan yet. Ask for resources first.")
            elif input("Apply the plan above? (yes/no) ").lower() == "yes":
                code, _ = tf.apply(project.dir)
                print("Done." if code == 0 else "Apply failed.")
        elif text == "/destroy":
            if input(f"DESTROY everything in '{name}'? Type the project name: ") == name:
                tf.destroy(project.dir)
                project.spec["resources"] = []
                project.state_file.write_text(json.dumps(project.spec, indent=2))
        else:
            messages.append({"role": "user", "content": text})
            chat_turn(project, messages)


if __name__ == "__main__":
    main()
