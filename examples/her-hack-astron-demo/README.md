---
id: her-hack-astron-demo
title: Her Hack Astron Demo
description: Turns a hackathon idea into a structured Astron project brief with goals, workflow outline, and demo checklist.
category: productivity
features:
  - Captures a raw hackathon idea in plain language
  - Expands it into a structured project brief
  - Produces a lightweight demo checklist for delivery
author: FenjuFu
sourceUrl: https://awesome-astron-workflow.dev/activities/astron-industrial-intelligence-hackathon
dslVersion: v1
event: Astron 产业智变黑客松
---

# Her Hack Astron Demo

A lightweight example for the Astron hackathon. Give it a rough idea, problem statement, or industry scenario,
and it rewrites the input into a clearer project brief that is easier to pitch, implement, and demo.

## How it works

**start → LLM → end.** The workflow accepts a short scenario description, asks the model to organize the idea,
and returns a concise output with project goals, user value, workflow outline, and a demo checklist.

## Dependencies

- **Models**: any chat-capable model configured in your Astron environment
- **Plugins / skills**: none required for this demo example
- **Knowledge bases**: none

## Import & run

1. In Astron Agent, create a workflow and import `workflow.yml` from this directory.
2. Bind the model node to an available chat model in your own environment.
3. Enter a hackathon concept such as an industrial QA bot, maintenance copilot, or workflow automation helper.
4. Run the flow and adapt the generated brief into your final demo or proposal.

## Notes

This example intentionally keeps the structure small so contributors can fork it during the hackathon and replace it
with their own exported workflow later.

