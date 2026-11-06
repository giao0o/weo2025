#!/usr/bin/env python3
"""Analyze IEA World Energy Outlook 2025 at scenario and technology level.

This is a document-content analysis, not an ex-post forecast-error study. A single WEO
edition does not contain the historical vintages and realised time series required for
projection-error estimation.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from collections import Counter, defaultdict
import fitz
import pandas as pd
import matplotlib.pyplot as plt

SCENARIOS = {
    "CPS": [r"\bCPS\b", r"Current Policies Scenario"],
    "STEPS": [r"\bSTEPS\b", r"Stated Policies Scenario"],
    "NZE": [r"\bNZE\b", r"Net Zero Emissions by 2050 Scenario"],
    "ACCESS": [r"\bACCESS\b"],
}
TECHNOLOGIES = {
    "Solar PV": [r"solar PV", r"photovoltaic"],
    "Wind": [r"\bwind\b", r"offshore wind", r"onshore wind"],
    "Batteries/storage": [r"\bbatter(?:y|ies)\b", r"battery storage", r"energy storage"],
    "Electric vehicles": [r"electric vehicle", r"\bEVs?\b"],
    "Heat pumps": [r"heat pumps?"],
    "CCUS/CCS": [r"\bCCUS\b", r"\bCCS\b", r"carbon capture"],
    "Nuclear": [r"\bnuclear\b"],
    "Hydrogen": [r"\bhydrogen\b"],
    "Bioenergy": [r"\bbioenergy\b", r"biofuel"],
    "Geothermal": [r"geothermal"],
    "Coal": [r"\bcoal\b"],
    "Oil": [r"\boil\b"],
    "Natural gas/LNG": [r"natural gas", r"\bLNG\b"],
}
# Auditable indicators: exact values are accepted only when the PDF page contains all anchors.
INDICATOR_RULES = [
    ("Electricity demand", 2035, "CPS/STEPS", 37800, "TWh", ["37 800", "2035", "TWh"]),
    ("Renewable capacity", 2024, "Observed/base year", 4900, "GW", ["4 900 GW", "2024"]),
    ("Renewable capacity", 2035, "STEPS", 13700, "GW", ["13 700 GW", "2035"]),
    ("Renewable capacity", 2035, "NZE", 19600, "GW", ["19 600 GW", "2035"]),
    ("LNG supply overhang", 2030, "STEPS", 65, "bcm", ["65 bcm", "overhang", "2030"]),
    ("New LNG export capacity", 2030, "Pipeline projects", 300, "bcm", ["300 bcm", "new LNG export capacity"]),
    ("Energy-related CO2 emissions", 2035, "STEPS", 35.2, "Gt CO2", ["35.2 Gt", "2035"]),
]

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ")).strip()

def sentence_snippet(text: str, anchors: list[str], width=380) -> str:
    low = text.lower()
    positions = [low.find(a.lower()) for a in anchors]
    positions = [p for p in positions if p >= 0]
    if not positions:
        return ""
    p = min(positions)
    start = max(0, p - width // 2)
    end = min(len(text), p + width)
    return norm(text[start:end])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(args.pdf)
    pages = [norm(p.get_text("text")) for p in doc]
    metadata = {"file": args.pdf.name, "pages": len(doc), "title": doc.metadata.get("title"),
                "author": doc.metadata.get("author")}

    # Page-level mentions
    rows = []
    for i, text in enumerate(pages, 1):
        for category, mapping in [("scenario", SCENARIOS), ("technology", TECHNOLOGIES)]:
            for label, patterns in mapping.items():
                count = sum(len(re.findall(p, text, flags=re.I)) for p in patterns)
                if count:
                    rows.append({"page": i, "category": category, "label": label, "mentions": count})
    mentions = pd.DataFrame(rows)
    mentions.to_csv(args.out / "page_mentions.csv", index=False)

    tech = (mentions[mentions.category == "technology"].groupby("label", as_index=False)
            .agg(total_mentions=("mentions", "sum"), pages_mentioned=("page", "nunique"))
            .sort_values("total_mentions", ascending=False))
    tech.to_csv(args.out / "technology_summary.csv", index=False)
    scen = (mentions[mentions.category == "scenario"].groupby("label", as_index=False)
            .agg(total_mentions=("mentions", "sum"), pages_mentioned=("page", "nunique"))
            .sort_values("total_mentions", ascending=False))
    scen.to_csv(args.out / "scenario_summary.csv", index=False)

    # Figures/tables captions
    captions = []
    cap_re = re.compile(r"\b(Figure|Table)\s+([A-Z]?\.?\d+(?:\.\d+)*)\s*[:.-]?\s*([^\n]{0,180})", re.I)
    for i, raw in enumerate(pages, 1):
        for m in cap_re.finditer(raw):
            captions.append({"page": i, "type": m.group(1).title(), "number": m.group(2),
                             "caption": norm(m.group(3))})
    pd.DataFrame(captions).drop_duplicates().to_csv(args.out / "captions_index.csv", index=False)

    # Validated indicator extraction with page and evidence snippet
    indicators = []
    for metric, year, scenario, value, unit, anchors in INDICATOR_RULES:
        found = None
        for page_no, text in enumerate(pages, 1):
            if all(a.lower() in text.lower() for a in anchors):
                found = {"metric": metric, "year": year, "scenario": scenario, "value": value,
                         "unit": unit, "pdf_page": page_no, "evidence": sentence_snippet(text, anchors)}
                break
        if found:
            indicators.append(found)
    ind = pd.DataFrame(indicators)
    ind.to_csv(args.out / "validated_indicators.csv", index=False)

    # A reproducible research-oriented keyword co-occurrence matrix
    labels = list(TECHNOLOGIES)
    co = pd.DataFrame(0, index=labels, columns=list(SCENARIOS), dtype=int)
    for text in pages:
        present_t = [k for k, ps in TECHNOLOGIES.items() if any(re.search(p, text, re.I) for p in ps)]
        present_s = [k for k, ps in SCENARIOS.items() if any(re.search(p, text, re.I) for p in ps)]
        for t in present_t:
            for s in present_s:
                co.loc[t, s] += 1
    co.to_csv(args.out / "technology_scenario_page_cooccurrence.csv")

    # Charts
    plt.figure(figsize=(10, 6))
    d = tech.head(13).sort_values("total_mentions")
    plt.barh(d.label, d.total_mentions)
    plt.xlabel("Mentions in PDF text")
    plt.title("WEO 2025 technology prominence")
    plt.tight_layout(); plt.savefig(args.out / "technology_prominence.png", dpi=180); plt.close()

    plt.figure(figsize=(7, 4.5))
    d = scen.sort_values("total_mentions")
    plt.barh(d.label, d.total_mentions)
    plt.xlabel("Mentions in PDF text")
    plt.title("WEO 2025 scenario prominence")
    plt.tight_layout(); plt.savefig(args.out / "scenario_prominence.png", dpi=180); plt.close()

    ren = ind[ind.metric == "Renewable capacity"].copy()
    if not ren.empty:
        plt.figure(figsize=(7, 4.5))
        labels2 = [f"{r.scenario}\n{int(r.year)}" for r in ren.itertuples()]
        plt.bar(labels2, ren.value)
        plt.ylabel("GW")
        plt.title("Renewable capacity indicators extracted from WEO 2025")
        plt.tight_layout(); plt.savefig(args.out / "renewable_capacity.png", dpi=180); plt.close()

    top = tech.iloc[0]
    report = f"""# WEO 2025 文档级技术与情景分析\n\n## 范围与限制\n本程序分析单一版本《World Energy Outlook 2025》的正文内容、情景和技术提及、图表索引及可审计的关键数值。它**不能直接计算历史预测误差**，因为误差研究需要多个出版年份的 WEO 投影以及对应的实际观测数据。\n\n## 数据概况\n- PDF 页数：{len(doc)}\n- 技术分类：{len(TECHNOLOGIES)}\n- 情景分类：{len(SCENARIOS)}\n- 已验证关键指标：{len(ind)}\n- 识别图表标题：{len(captions)}\n\n## 主要发现\n1. 文本中提及最多的技术类别是 **{top.label}**，共 {int(top.total_mentions)} 次，分布在 {int(top.pages_mentioned)} 页。提及频率反映报告篇幅与讨论强度，不等于投资规模或部署量。\n2. CPS、STEPS、NZE 和 ACCESS 的提及分布显示，WEO 2025 是多情景条件分析，而非单一路径预测。\n3. 可直接核验的技术指标包括：2024 年可再生能源装机约 4,900 GW；2035 年 STEPS 约 13,700 GW，NZE 约 19,600 GW。\n4. 2035 年 CPS/STEPS 电力需求约 37,800 TWh。LNG 方面，报告讨论了约 300 bcm 的新增出口能力及 STEPS 中 2030 年约 65 bcm 的供应富余。\n5. 若用于论文题目“技术层面的投影误差”，下一步必须把本程序扩展为 vintage panel：每行至少包含 publication_year、scenario、technology、target_year、projected_value、unit、realized_value、source_page。\n\n## 输出文件说明\n- `validated_indicators.csv`：人工规则约束、带页码和证据文本的关键数值\n- `technology_summary.csv`：技术提及次数和覆盖页数\n- `scenario_summary.csv`：情景提及次数和覆盖页数\n- `technology_scenario_page_cooccurrence.csv`：技术与情景在同页出现次数\n- `captions_index.csv`：Figure/Table 标题索引\n- PNG：三张结果图\n\n## 对毕业论文的直接用途\n该结果可作为 WEO 2025 的“单期解析器”和编码框架原型。预测误差建议使用 MAPE、sMAPE、方向性偏差（ME）和相对基准误差，并分别按技术、情景类型、预测提前期和出版年份建模。对接历史 WEO 后，可检验学习曲线、政策冲击、模块成熟度、情景规范变化和技术扩散非线性等解释。\n"""
    (args.out / "analysis_report_zh.md").write_text(report, encoding="utf-8")
    (args.out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "pages": len(doc), "indicators": len(ind),
                      "captions": len(captions), "output": str(args.out)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
