# Extraction prompt, version extract_v1

Store with every result: prompt version `extract_v1`, provider, exact model id. Temperature 0.
The model sees only the clause. No standard data is passed. Spans are character offsets into the clause.
All examples below are synthetic and were checked with the span-validator skill.

## System prompt
```
You extract structured data from one tender clause. Output JSON only, matching the schema.
Rules:
- Copy citation text exactly as written. Never correct, complete or invent an IS number, part or year.
- If a field is absent, return null or an empty list.
- Report phrases that name quality or standards without a number (for example "ISI quality") under vague_phrases.
- Return character spans that are exact substrings of the clause.
- The clause may be in Hindi, English or both. Do not translate the spans.
- Set canonical_product_id to null. Product mapping is done elsewhere.
```

## Schema
Keys: clause_id, language (hi|en|mixed), products[{text, span, canonical_product_id}], citations[{raw, span, is_number, part, year}], vague_phrases[{text, span}], requirements[{text, span}].

## Worked examples (synthetic)
Covers: English with part and year, dashed number, vague wording, product not in dataset, typo kept as written, Hindi, mixed, no citation.

Clause c1:
```
The supplier shall deliver 50 laptops conforming to IS 13252 (Part 1): 2010.
```
Output:
```json
{
  "clause_id": "c1",
  "language": "en",
  "products": [
    {
      "text": "laptops",
      "span": [
        30,
        37
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [
    {
      "raw": "IS 13252 (Part 1): 2010",
      "span": [
        52,
        75
      ],
      "is_number": "IS 13252",
      "part": "1",
      "year": 2010
    }
  ],
  "vague_phrases": [],
  "requirements": [
    {
      "text": "conforming to IS 13252 (Part 1): 2010",
      "span": [
        38,
        75
      ]
    }
  ]
}
```

Clause c2:
```
Microwave ovens shall conform to IS 302-2-25.
```
Output:
```json
{
  "clause_id": "c2",
  "language": "en",
  "products": [
    {
      "text": "Microwave ovens",
      "span": [
        0,
        15
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [
    {
      "raw": "IS 302-2-25",
      "span": [
        33,
        44
      ],
      "is_number": "IS 302-2-25",
      "part": null,
      "year": null
    }
  ],
  "vague_phrases": [],
  "requirements": [
    {
      "text": "shall conform to IS 302-2-25",
      "span": [
        16,
        44
      ]
    }
  ]
}
```

Clause c3:
```
The IT equipment shall be of ISI quality.
```
Output:
```json
{
  "clause_id": "c3",
  "language": "en",
  "products": [
    {
      "text": "IT equipment",
      "span": [
        4,
        16
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [],
  "vague_phrases": [
    {
      "text": "ISI quality",
      "span": [
        29,
        40
      ]
    }
  ],
  "requirements": []
}
```

Clause c4:
```
The supplier shall deliver 20 portable air purifiers rated for 30 square metres.
```
Output:
```json
{
  "clause_id": "c4",
  "language": "en",
  "products": [
    {
      "text": "portable air purifiers",
      "span": [
        30,
        52
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [],
  "vague_phrases": [],
  "requirements": [
    {
      "text": "rated for 30 square metres",
      "span": [
        53,
        79
      ]
    }
  ]
}
```

Clause c5:
```
IT equipment shall conform to IS 13253 (Part 1): 2010.
```
Output:
```json
{
  "clause_id": "c5",
  "language": "en",
  "products": [
    {
      "text": "IT equipment",
      "span": [
        0,
        12
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [
    {
      "raw": "IS 13253 (Part 1): 2010",
      "span": [
        30,
        53
      ],
      "is_number": "IS 13253",
      "part": "1",
      "year": 2010
    }
  ],
  "vague_phrases": [],
  "requirements": [
    {
      "text": "IT equipment shall conform to IS 13253 (Part 1): 2010",
      "span": [
        0,
        53
      ]
    }
  ]
}
```

Clause c6:
```
आपूर्तिकर्ता 50 लैपटॉप की आपूर्ति करेगा। लैपटॉप IS 13252 (भाग 1): 2010 के अनुरूप होंगे।
```
Output:
```json
{
  "clause_id": "c6",
  "language": "hi",
  "products": [
    {
      "text": "लैपटॉप",
      "span": [
        16,
        22
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [
    {
      "raw": "IS 13252 (भाग 1): 2010",
      "span": [
        48,
        70
      ],
      "is_number": "IS 13252",
      "part": "1",
      "year": 2010
    }
  ],
  "vague_phrases": [],
  "requirements": []
}
```

Clause c7:
```
Supply of laptops (लैपटॉप) as per IS/IEC 62368 Part 1: 2023 आवश्यक है।
```
Output:
```json
{
  "clause_id": "c7",
  "language": "mixed",
  "products": [
    {
      "text": "laptops",
      "span": [
        10,
        17
      ],
      "canonical_product_id": null
    },
    {
      "text": "लैपटॉप",
      "span": [
        19,
        25
      ],
      "canonical_product_id": null
    }
  ],
  "citations": [
    {
      "raw": "IS/IEC 62368 Part 1: 2023",
      "span": [
        34,
        59
      ],
      "is_number": "IS/IEC 62368",
      "part": "1",
      "year": 2023
    }
  ],
  "vague_phrases": [],
  "requirements": []
}
```

Clause c8:
```
All items shall be as per BIS standards.
```
Output:
```json
{
  "clause_id": "c8",
  "language": "en",
  "products": [],
  "citations": [],
  "vague_phrases": [
    {
      "text": "as per BIS standards",
      "span": [
        19,
        39
      ]
    }
  ],
  "requirements": []
}
```
