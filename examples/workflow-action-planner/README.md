---
id: workflow-action-planner
title: Workflow Action Planner
description: Turns a goal or meeting note into a prioritized, owner-ready action checklist.
category: productivity
features:
  - Extracts concrete actions from unstructured notes
  - Orders work by dependency and urgency
  - Flags missing owners, dates, and decisions
author: FenjuFu
sourceUrl: ""
dslVersion: v1
event: ""
---

# Workflow Action Planner

Paste a project goal, meeting note, or handoff message and get a short checklist that is ready to copy into a task tracker. The workflow keeps unknown owners and dates visible as `TBD` instead of guessing.

## How it works

**start ? LLM ? output.** The model extracts actions, groups related work, orders the list by dependency and urgency, and reports open questions separately.

## Dependencies

- **Models**: a Spark chat model (credentials scrubbed)
- **Plugins / skills**: none
- **Knowledge bases**: none

## Import & run

1. In Astron Agent, create a workflow ? **Import** ? choose `workflow.yml`.
2. Replace the `YOUR_APP_ID` placeholder with your own Spark credentials.
3. Paste a goal or meeting note as the workflow input and run it.

> The exported DSL contains a placeholder app id and no live credentials.

## Example input

```text
We need a beta release next Friday. Ming will verify the login flow, but the API contract is still undecided.
```

The output separates the release checklist, the owner for each action, and the unresolved API-contract decision.
