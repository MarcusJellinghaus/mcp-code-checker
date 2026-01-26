---
workflow-stage: issue-discussion
suggested-next: discuss -> issue_update -> issue_approve
---

# Analyse GitHub Issue

Fetch a GitHub issue and analyze its requirements, feasibility, and potential implementation approaches.

## Instructions

First, fetch the issue details:
```bash
gh issue view $ARGUMENTS
```

Then analyze the issue:

Can we discuss this requirement / implementation idea and its feasibility?
Please also look at the code base to understand the context (using the different tools with access to the project directory).
Do not provide code yet!

At the end of our discussion, I want to have an even better issue description.

**Focus on:**
- Understanding the problem/feature request
- Technical feasibility
- Potential implementation approaches
- Questions that need clarification
- Impact on existing code
