# WEO 2025 Analysis Package

Run:

```bash
python analyze_weo2025.py WorldEnergyOutlook2025.pdf --out results
```

The program performs document-level scenario and technology analysis, produces auditable CSV files and charts, and clearly separates this from a historical projection-error study.

To extend it for the thesis, collect historical WEO editions and realised data, then create a panel with: `publication_year, scenario, technology, target_year, projected_value, unit, realised_value, source_page`.
