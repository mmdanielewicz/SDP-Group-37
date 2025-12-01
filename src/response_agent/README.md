## Response Agent Overview
The Response Agent is responsible for taking the full JSON output from the Orchestration layer and generating a netural-language summary for the user.

The Response Agent DOES NOT run routing or shelter logic.

The Response Agent ONLY takes the JSON computed by the Orchestration Agent and summarizes it.

## What the Response Agent Receives

{
  "query": "...",
  "shelter_results": { ... },
  "routing_results": { ... }
}
