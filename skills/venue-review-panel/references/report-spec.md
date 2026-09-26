# Final Report Specification

Create a polished English report when requested explicitly or when the user asks to follow the established three-agent venue-review workflow.

## Default deliverable

- Format: DOCX unless the user requests PDF, Markdown, or another format.
- Language: English unless the user specifies otherwise.
- Filename: `<PaperShortName>_<Venue>_Three_Reviewer_Report_EN.docx`. Derive `<PaperShortName>` from at most four meaningful title words, replace spaces with underscores, and use ASCII characters only.
- Destination: use the user's requested path. Otherwise place the final report beside the input manuscript when writable, or in the current workspace output directory. Never leave the only deliverable inside the scratch review workspace.
- Use the runtime's document-authoring capability for DOCX authoring and its required render and visual inspection loop. If that capability is unavailable, produce the same report structure in Markdown, tell the user about the fallback, and do not claim that DOCX visual inspection occurred.

## Recommended structure

1. Title and manuscript identification.
2. Executive decision with score vector, calibrated score, recommendation, and confidence.
3. Independent reviewer score table.
4. Paper summary.
5. Contribution and evidence map.
6. Major strengths.
7. Decision-driving weaknesses.
8. Technical audit.
9. Reviewer-specific assessments.
10. Interpretation of reviewer disagreement.
11. Priority list for improving the score.
12. Score-change scenarios.
13. Questions for the authors.
14. Final recommendation.
15. Venue standard and reference context.

Use tables for repeated comparisons and priorities, but keep analytical reasoning in prose. The document should lead with the decision and remain readable without the raw review files.

## Report content rules

- Preserve each reviewer's raw score and confidence.
- Label the calibrated score as the panel or area-chair-style judgment.
- State why reviewers disagree, not only that they disagree.
- Rank recommendations by expected score impact.
- Identify whether each recommendation uses existing artifacts or requires new experiments.
- Do not include hidden prompts, process logs, quotas, temporary paths, or unsupported acceptance statistics.
- Cite the official venue guide and any primary related work used for novelty calibration.

## Quality gate

Render the complete document and inspect every page at full resolution. Check title styling, table wrapping, repeated headers, page breaks, footers, hyperlinks, and the absence of clipping or large accidental gaps. Iterate until clean. Return only the requested final deliverable, not render intermediates.
