# Section Templates

Move sequences shared by the five first-author papers in `exemplars.md`, with how often each move appears. They describe the author's habits, not facts to supply. Use a move only when the facts you were given support it, including claims about prior work, priority, causes, results, releases, and future plans; leave out a move they do not support, and keep every stated scope and qualifier. A move marked optional appears in some papers only, and a draft does not need every move.

## Abstract (about 170 to 250 words, one paragraph)

1. Problem hook, never the field's importance. A question that names the input and the constraint (MetaOD, HPOD, SUOD: "Given X, how can we ... without any labels?"), or a concession and gap (ELECT: "there exists no shortage of X, yet Y is understudied"; ADMoE: "existing works rely on clean labels").
2. Contribution sentence: "In this work, we tackle/propose", the method named and its acronym coined in the same sentence. Optional flat "first" claim, only when the facts establish priority.
3. Optional challenge: what makes the problem hard, as two inline reasons ("since (i) model evaluation is infeasible ..., and (ii) model comparison is infeasible ...").
4. Mechanism in plain active verbs with the method as subject ("capitalizes on", "carries over"), core idea first, then a second ingredient ("To capture X, we introduce ...", "Uniquely, ...", "To further juice out ...").
5. Evidence in words or one rounded figure: "Extensive experiments show that X significantly outperforms ...", with the baselines named by kind.
6. Optional closer: the code release when there is one, or an efficiency or generality sentence the facts support. Never limitations, future work, or a significance flourish.

## Introduction (five to seven paragraphs)

1. Opening that ends on the gap. Either start at the gap ("Although a long list of X has been proposed, how to Y remains underexplored") or define the task with about three applications, then concede that many methods exist. Back the gap with one piece of evidence where the facts hold one.
2. Working case: one to three sentences on what works in the easy setting (supervised selection, clean labels).
3. Turn: "However," or "In contrast," and why that approach does not transfer here, often as inline reasons; end on a flat verdict the facts support ("Consequently, there has been no principled work on ...").
4. Own approach: "In this work, we", the mechanism after "In a nutshell,", a "first" claim with "(to the best of our knowledge)" only when the facts establish priority, and a scope remark ("We remark that X is strictly a Y technique, rather than a new detector") when the work could be taken for a neighboring kind.
5. Optional positioning: an analogy to a neighboring problem and how this one differs.
6. Optional results preview under a bold run-in label ("**Performance.**").
7. "In summary, the key contributions of this work include:" then the supported contributions, usually three to five, each a bold noun-phrase head and full "We ..." sentences, effectiveness last when there are results. When the facts include a code or data release, add a one-sentence bold "**Reproducibility.**" line. No roadmap paragraph.

## Conclusion (about 70 to 250 words, median 125, usually one paragraph)

1. The claim in near-abstract wording ("We addressed X without relying on any labels ..."), with "for the first time" only when the facts establish priority.
2. The mechanism in a clause or two, often offline-then-online.
3. Optional "Notably," sentence on what sets the method apart.
4. One evidence sentence, without numbers.
5. Optional release sentence when there is a release; a scoped limitation where the facts carry one.
6. A future-work sentence when the facts name a direction ("Future work will consider ..."). No limitations paragraph, broader impact, or closing flourish.
