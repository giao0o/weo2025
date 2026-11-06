# WEO 2025 文档级技术与情景分析

## 范围与限制
本程序分析单一版本《World Energy Outlook 2025》的正文内容、情景和技术提及、图表索引及可审计的关键数值。它**不能直接计算历史预测误差**，因为误差研究需要多个出版年份的 WEO 投影以及对应的实际观测数据。

## 数据概况
- PDF 页数：519
- 技术分类：13
- 情景分类：4
- 已验证关键指标：6
- 识别图表标题：556

## 主要发现
1. 文本中提及最多的技术类别是 **Natural gas/LNG**，共 766 次，分布在 228 页。提及频率反映报告篇幅与讨论强度，不等于投资规模或部署量。
2. CPS、STEPS、NZE 和 ACCESS 的提及分布显示，WEO 2025 是多情景条件分析，而非单一路径预测。
3. 可直接核验的技术指标包括：2024 年可再生能源装机约 4,900 GW；2035 年 STEPS 约 13,700 GW，NZE 约 19,600 GW。
4. 2035 年 CPS/STEPS 电力需求约 37,800 TWh。LNG 方面，报告讨论了约 300 bcm 的新增出口能力及 STEPS 中 2030 年约 65 bcm 的供应富余。
5. 若用于论文题目“技术层面的投影误差”，下一步必须把本程序扩展为 vintage panel：每行至少包含 publication_year、scenario、technology、target_year、projected_value、unit、realized_value、source_page。

## 输出文件说明
- `validated_indicators.csv`：人工规则约束、带页码和证据文本的关键数值
- `technology_summary.csv`：技术提及次数和覆盖页数
- `scenario_summary.csv`：情景提及次数和覆盖页数
- `technology_scenario_page_cooccurrence.csv`：技术与情景在同页出现次数
- `captions_index.csv`：Figure/Table 标题索引
- PNG：三张结果图

## 对毕业论文的直接用途
该结果可作为 WEO 2025 的“单期解析器”和编码框架原型。预测误差建议使用 MAPE、sMAPE、方向性偏差（ME）和相对基准误差，并分别按技术、情景类型、预测提前期和出版年份建模。对接历史 WEO 后，可检验学习曲线、政策冲击、模块成熟度、情景规范变化和技术扩散非线性等解释。
