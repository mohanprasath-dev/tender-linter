from pathlib import Path

from packages.data.curator import generate_coverage_report, get_needed_cells


def test_get_needed_cells_identifies_missing_provenance() -> None:
    seed_dir = Path(__file__).resolve().parent.parent / "packages" / "data" / "seed"
    needed = get_needed_cells(seed_dir)

    # standards.csv and product_standard_map.csv have known missing fields
    assert "standards.csv" in needed
    assert "product_standard_map.csv" in needed

    std_cells = needed["standards.csv"]
    assert any("catalogue_url" in cell["missing"] for cell in std_cells)
    assert any("verified_by" in cell["missing"] for cell in std_cells)


def test_generate_coverage_report_format() -> None:
    seed_dir = Path(__file__).resolve().parent.parent / "packages" / "data" / "seed"
    report = generate_coverage_report(seed_dir)

    assert "Coverage Report" in report
    assert "products" in report.lower()
    assert "standards" in report.lower()
    assert "verified" in report.lower()
