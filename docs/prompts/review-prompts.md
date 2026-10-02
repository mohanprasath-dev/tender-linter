# Review and Utility Prompts

## Second-person row check (curator)
```
I will paste a data row and the metadata I read from the official page. Compare field by field. Report only mismatches and empty fields I should leave empty. Do not fill anything in. Do not suggest values from memory.
```

## Hindi message review request (to a fluent reviewer)
```
Please review each Hindi message for meaning, tone and consistency with the English. Do not add claims. Keep "verified date" and the source link wording. Return corrections as a table: id, current, proposed, reason.
```

## Deck claim check
```
Here is the slide text. For each claim, give: slide, claim, the built feature or verified fact it maps to (with file or row), or UNMAPPED. Remove UNMAPPED claims. Check: six slides, no em dashes, no bare percentages, model name and bake-off date present.
```

## Release gate summary
```
Run the evaluation. Print: rule recall, false alarms on clean controls, abstain correctness, invented-citation count, evidence completeness, each as "X of Y on test set Z". List any planted defect that previously passed and now fails.
```
