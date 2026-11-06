# Abstract draft

**Title:** What share of field values stated by a language model match the NTSB record? A sample of public occurrence narratives

Language models can summarise an aviation occurrence and still state a fact the source narrative does not support. This study measured that risk on public records rather than on invented claims. One language model (Qwen/Qwen2.5-0.5B-Instruct) read a random sample of 200 narratives from the NTSB pre-2008 aviation database (27443 records, 1974–2007) and was asked to state four values: highest injury, basic weather, light, and whether the event was a mid-air collision. It was instructed to answer unknown when the narrative did not say. Each answer was compared with the structured field stored for the same event. Of 800 field slots, the model gave a code for 669 and abstained on 131. Among the codes it gave, 350 matched the structured field (52.3%) and 319 did not. Matched rates by field, among answered claims, were 58.4% for injury, 79.7% for weather, 84.1% for light and 6.1% for mid-air. On a held-out part of the sample, a separate text classifier trained only on other narratives assigned a support score to each stated code. For midair, 0.0% of 37 mismatched held-out claims were above the cutoff, and 100.0% of 3 matched claims were. The language model saw only the sample, so these rates are not a performance figure for the full database. No investigator reviewed the statements. Nothing here is a basis for accepting a summary in an investigation, and the calibration rule that turns a support score into a cutoff is not described in this abstract.

**Keywords:** aviation safety; large language models; accident narratives; claim check; NTSB

Words in abstract: 244
