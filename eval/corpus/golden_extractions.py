"""Deterministic ground-truth extractions for test corpus v1 (T01-T65).
Used by evaluation harness for deterministic CI regression gate.
"""

from packages.rules.schema import (
    CitationExtraction,
    ClauseExtraction,
    ProductExtraction,
    VaguePhraseExtraction,
)


def get_golden_extractions(row_id: str, clause_text: str = "") -> list[ClauseExtraction]:
    """Return deterministic, gold-standard extractions for row_id."""
    text = clause_text

    # --- Core Matrix T01 to T13 ---
    if row_id == "T01":
        return [
            ClauseExtraction(
                clause_id="T01",
                text=text or "The supplier shall deliver 50 laptops. The laptops shall conform to IS 13252 (Part 1): 2010.",
                products=[ProductExtraction(text="laptops", span=(30, 37), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(68, 92), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T02":
        return [
            ClauseExtraction(
                clause_id="T02",
                text=text or "The supplier shall deliver 50 laptops. The laptops shall conform to IS/IEC 62368 Part 1: 2023.",
                products=[ProductExtraction(text="laptops", span=(30, 37), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(68, 94), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T03":
        return [
            ClauseExtraction(
                clause_id="T03",
                text=text or "The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2019. Registration under the Compulsory Registration Scheme is required.",
                products=[ProductExtraction(text="laptops", span=(27, 34), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2019", span=(49, 75), is_number="IS/IEC 62368 Part 1", part="1", year=2019)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T04":
        return [
            ClauseExtraction(
                clause_id="T04",
                text=text or "The supplier shall deliver 10 microwave ovens conforming to IS 302-2-25.",
                products=[ProductExtraction(text="microwave ovens", span=(30, 45), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(60, 71), is_number="IS 302-2-25")],
                mentions_certification=False,
            )
        ]
    elif row_id == "T05":
        return [
            ClauseExtraction(
                clause_id="T05",
                text=text or "The supplier shall deliver 10 microwave ovens. Registration under the Compulsory Registration Scheme is required.",
                products=[ProductExtraction(text="microwave ovens", span=(30, 45), canonical_product_id="Microwave ovens")],
                citations=[],
                mentions_certification=True,
            )
        ]
    elif row_id == "T06":
        return [
            ClauseExtraction(
                clause_id="T06",
                text=text or "The supplier shall deliver IT equipment of ISI quality.",
                products=[ProductExtraction(text="IT equipment", span=(27, 39), canonical_product_id="IT equipment (general)")],
                citations=[],
                vague_phrases=[VaguePhraseExtraction(text="ISI quality", span=(43, 54), phrase="ISI quality")],
            )
        ]
    elif row_id == "T07":
        return [
            ClauseExtraction(
                clause_id="T07",
                text=text or "The supplier shall deliver 20 portable air purifiers rated for 30 square metres.",
                products=[ProductExtraction(text="portable air purifiers", span=(30, 52), canonical_product_id=None)],
                citations=[],
            )
        ]
    elif row_id == "T08":
        return [
            ClauseExtraction(
                clause_id="T08",
                text=text or "The supplier shall deliver IT equipment conforming to IS 99999: 2015.",
                products=[ProductExtraction(text="IT equipment", span=(27, 39), canonical_product_id="IT equipment (general)")],
                citations=[CitationExtraction(raw="IS 99999: 2015", span=(54, 69), is_number="IS 99999", year=2015)],
            )
        ]
    elif row_id == "T09":
        return [
            ClauseExtraction(
                clause_id="T09_1",
                text="Clause 4.1: IT equipment shall conform to IS 13252 (Part 1): 2010.",
                products=[ProductExtraction(text="IT equipment", span=(12, 24), canonical_product_id="IT equipment (general)")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(43, 67), is_number="IS 13252 (Part 1)", part="1", year=2010)],
            ),
            ClauseExtraction(
                clause_id="T09_2",
                text="Clause 9.2: testing shall follow IS 13252 (Part 1): 2008.",
                products=[ProductExtraction(text="testing", span=(12, 19), canonical_product_id=None)],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2008", span=(33, 57), is_number="IS 13252 (Part 1)", part="1", year=2008)],
            ),
        ]
    elif row_id == "T10":
        return [
            ClauseExtraction(
                clause_id="T10",
                text=text or "The supplier shall deliver IT equipment conforming to IS 13253 (Part 1): 2010.",
                products=[ProductExtraction(text="IT equipment", span=(27, 39), canonical_product_id="IT equipment (general)")],
                citations=[CitationExtraction(raw="IS 13253 (Part 1): 2010", span=(54, 78), is_number="IS 13253", part="1", year=2010)],
            )
        ]
    elif row_id == "T11":
        return [
            ClauseExtraction(
                clause_id="T11",
                text=text or "The supplier shall deliver 10 microwave ovens conforming to IS 13252 (Part 1): 2010. Registration under the Compulsory Registration Scheme is required.",
                products=[ProductExtraction(text="microwave ovens", span=(30, 45), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(60, 84), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T12":
        return [
            ClauseExtraction(
                clause_id="T12",
                language="hi",
                text=text or "आपूर्तिकर्ता 50 लैपटॉप की आपूर्ति करेगा। लैपटॉप IS 13252 (भाग 1): 2010 के अनुरूप होंगे। अनिवार्य पंजीकरण योजना (CRS) के अंतर्गत पंजीकरण आवश्यक है।",
                products=[ProductExtraction(text="लैपटॉप", span=(16, 22), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (भाग 1): 2010", span=(47, 70), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T13":
        return [
            ClauseExtraction(
                clause_id="T13",
                text=text or "The supplier shall deliver 50 laptops conforming to IS/IEC 62368 Part 1: 2023. Registration under the Compulsory Registration Scheme is required.",
                products=[ProductExtraction(text="laptops", span=(27, 34), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(49, 75), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]

    # --- Clean Controls T14 to T25 ---
    elif row_id in ("T14", "T15", "T18", "T24", "T25"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T16":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="power adaptors for IT equipment", span=(0, 0), canonical_product_id="Power adaptors for IT equipment")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]
    elif row_id in ("T17", "T23"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="microwave ovens", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(0, 0), is_number="IS 302-2-25")],
                mentions_certification=True,
            )
        ]
    elif row_id in ("T19", "T22"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T20":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="माइक्रोवेव ओवन", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(0, 0), is_number="IS 302-2-25")],
                mentions_certification=True,
            )
        ]
    elif row_id == "T21":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="पावर एडाप्टर", span=(0, 0), canonical_product_id="Power adaptors for IT equipment")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=True,
            )
        ]

    # --- Adversarial Cases T26 to T38 ---
    elif row_id == "T26":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="IT equipment", span=(0, 0), canonical_product_id="IT equipment (general)")],
                citations=[CitationExtraction(raw="IS 13253", span=(0, 0), is_number="IS 13253", part="1", year=2010)],
            )
        ]
    elif row_id in ("T27", "T28", "T31", "T33", "T35", "T37", "T38"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=False,
            )
        ]
    elif row_id in ("T29", "T32", "T34"):
        vague = [VaguePhraseExtraction(text="ISI quality", span=(0, 0), phrase="ISI quality")] if "ISI" in (text or "") or "बीआईएस" in (text or "") else []
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[],
                mentions_certification=False,
                vague_phrases=vague or [VaguePhraseExtraction(text="standard quality", span=(0, 0), phrase="as per BIS")],
            )
        ]
    elif row_id == "T30":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="IT equipment", span=(0, 0), canonical_product_id="IT equipment (general)")],
                citations=[CitationExtraction(raw="I S 1 3 2 5 2", span=(0, 0), is_number="IS 13253")],  # Near-match triggers R12
            )
        ]
    elif row_id == "T36":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="microwave ovens", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-24", span=(0, 0), is_number="IS 302-2-24")],  # Near match to IS 302-2-25
            )
        ]

    # --- Abstain Cases T39 to T50 (Unmapped Products) ---
    elif row_id in ("T39", "T40", "T41", "T42", "T43", "T44", "T45", "T46", "T47", "T48", "T49", "T50"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text=text[:30], span=(0, 0), canonical_product_id=None)],
                citations=[],
            )
        ]

    # --- Defect Cases T51 to T65 ---
    elif row_id in ("T51", "T64"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[],
                citations=[CitationExtraction(raw="IS 999: 1995", span=(0, 0), is_number="IS 999", year=1995)],
            )
        ]
    elif row_id in ("T52", "T59"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2018", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2018)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T53":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252: 2010", span=(0, 0), is_number="IS 13252", part=None, year=2010)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T54":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[],
                citations=[CitationExtraction(raw="IS 555 Part 1: 2015", span=(0, 0), is_number="IS 555", part="1", year=2015)],
            )
        ]
    elif row_id == "T55":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(0, 0), is_number="IS 302-2-25")],
                mentions_certification=True,
            )
        ]
    elif row_id == "T56":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="microwave ovens", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T57":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 88888: 2021", span=(0, 0), is_number="IS 88888", year=2021)],
                mentions_certification=False,
            )
        ]
    elif row_id in ("T58", "T60"):
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS/IEC 62368 Part 1: 2023", span=(0, 0), is_number="IS/IEC 62368 Part 1", part="1", year=2023)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T61":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="माइक्रोवेव ओवन", span=(0, 0), canonical_product_id="Microwave ovens")],
                citations=[CitationExtraction(raw="IS 302-2-25", span=(0, 0), is_number="IS 302-2-25")],
                mentions_certification=False,
            )
        ]
    elif row_id == "T62":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="लैपटॉप", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[],
                mentions_certification=False,
                vague_phrases=[VaguePhraseExtraction(text="बीआईएस गुणवत्ता", span=(0, 0), phrase="as per BIS")],
            )
        ]
    elif row_id == "T63":
        return [
            ClauseExtraction(
                clause_id="T63_1",
                text="Clause 2: Laptops conform to IS 13252 (Part 1): 2010.",
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            ),
            ClauseExtraction(
                clause_id="T63_2",
                text="Clause 8: Laptops conform to IS 13252 (Part 1): 2008.",
                products=[],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2008", span=(0, 0), is_number="IS 13252 (Part 1)", part="1", year=2008)],
            ),
        ]
    elif row_id == "T65":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text,
                products=[ProductExtraction(text="laptops", span=(0, 0), canonical_product_id="Laptop / notebook / tablet")],
                citations=[],
                mentions_certification=False,
            )
        ]
    elif row_id == "T66":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "The contractor shall supply 500 bags of Ordinary Portland Cement conforming to IS 269: 2015 bearing the mandatory ISI mark as per Cement Quality Control Order.",
                products=[ProductExtraction(text="Ordinary Portland Cement", span=(37, 61), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 269: 2015", span=(76, 88), is_number="IS 269", year=2015)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T67":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "ठेकेदार 200 बैग ऑर्डिनरी पोर्टलैंड सीमेंट की आपूर्ति करेगा जो IS 269: 2015 के अनुरूप होगी और अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO) के तहत प्रमाणित होगी।",
                products=[ProductExtraction(text="ऑर्डिनरी पोर्टलैंड सीमेंट", span=(16, 40), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 269: 2015", span=(61, 73), is_number="IS 269", year=2015)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T68":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "The vendor shall deliver 100 bags of cement (सीमेंट) conforming to IS 269: 2015 with mandatory BIS certification mark.",
                products=[ProductExtraction(text="cement (सीमेंट)", span=(37, 52), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 269: 2015", span=(68, 80), is_number="IS 269", year=2015)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T69":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "The supplier shall deliver 300 bags of Ordinary Portland Cement conforming to IS 269: 2015.",
                products=[ProductExtraction(text="Ordinary Portland Cement", span=(39, 63), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 269: 2015", span=(78, 90), is_number="IS 269", year=2015)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T70":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "The contractor shall supply Ordinary Portland Cement conforming to IS 269: 1989 with ISI mark certification as per QCO.",
                products=[ProductExtraction(text="Ordinary Portland Cement", span=(28, 52), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 269: 1989", span=(67, 79), is_number="IS 269", year=1989)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T71":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "आपूर्तिकर्ता 500 बोरी साधारण पोर्टलैंड सीमेंट IS 269: 2015 के अनुरूप प्रदान करेगा।",
                products=[ProductExtraction(text="साधारण पोर्टलैंड सीमेंट", span=(21, 44), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 269: 2015", span=(45, 57), is_number="IS 269", year=2015)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T72":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "The tenderer shall supply 400 bags of Portland cement for foundation work.",
                products=[ProductExtraction(text="Portland cement", span=(38, 53), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[],
                mentions_certification=False,
            )
        ]
    elif row_id == "T73":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "The supplier shall supply 200 bags of Ordinary Portland Cement conforming to IS 13252 (Part 1): 2010 with ISI mark.",
                products=[ProductExtraction(text="Ordinary Portland Cement", span=(38, 62), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS 13252 (Part 1): 2010", span=(77, 101), is_number="IS 13252 (Part 1)", part="1", year=2010)],
                mentions_certification=True,
            )
        ]
    elif row_id == "T74":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "निर्माण कार्य हेतु २०० बोरी सीमेंट IS २६९: २०१५ के अनुरूप आपूर्ति की जाएगी।",
                products=[ProductExtraction(text="सीमेंट", span=(27, 33), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[CitationExtraction(raw="IS २६९: २०१५", span=(34, 46), is_number="IS 269", year=2015)],
                mentions_certification=False,
            )
        ]
    elif row_id == "T75":
        return [
            ClauseExtraction(
                clause_id=row_id,
                text=text or "Contractor must provide Ordinary Portland Cement of best ISI quality as per government norms.",
                products=[ProductExtraction(text="Ordinary Portland Cement", span=(24, 48), canonical_product_id="Ordinary Portland Cement (OPC)")],
                citations=[],
                vague_phrases=[VaguePhraseExtraction(text="ISI quality", span=(57, 68), phrase="ISI quality")],
                mentions_certification=False,
            )
        ]

    return []
