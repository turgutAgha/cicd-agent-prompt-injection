# Prevalence

Read-only public GitHub API metadata (step 6). Counts how many public repos
adopt each target CI action / workflow, to contextualize the technique matrix
with real-world reach.

- **Metadata only.** No cloning, no payloads, no interaction with third-party
  repos or services. Just adoption counts from the public search API.
- Output: `adoption.csv` (`action`, `search_query`, `repo_count`, `collected_at`).

Held until steps 1–3 are approved and the oracle is verified.
