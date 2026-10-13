# Payloads

One file per injection **vector** (step 4). Each file holds several phrasing
**variants** as *data*, not code — the harness loads them and injects each into
testbed content.

Planned vector files (held until oracle is verified):

| File                      | Vector — where untrusted text enters the agent |
|---------------------------|------------------------------------------------|
| `issue_comment.yaml`      | Text of an issue / issue comment               |
| `pr_body.yaml`            | Pull request description body                   |
| `code_comment.yaml`       | Comment inside a source file in the diff        |
| `readme.yaml`             | Repo `README` content the agent reads          |
| `commit_msg.yaml`         | Commit message                                 |
| `filename.yaml`           | A crafted file name / path                     |
| `dependency_metadata.yaml`| Package / action metadata fields               |

Each variant references the oracle in one of two ways:
- Instructs the agent to emit the canary token `CANARY_{uuid}` (token injected per trial).
- Instructs the agent to call a flagged tool (e.g. `post_external_webhook`).

**Scope reminder:** these payloads are only ever injected into the local testbed
content in this project. They are never sent to external repos or services.
