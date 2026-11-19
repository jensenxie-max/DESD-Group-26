# Sprint 2 contribution record

本记录按四人既定分工归集截至 2026 年 11 月 18 日的已交付成果，整理日期为 2026 年 11 月 19 日。小组提供的贡献矩阵为 [Contribution-Matrix.docx](Contribution-Matrix.docx)。

总体比例按小组提供的矩阵记录：Jiaqi、Yunze 各 27.55%，Jilong、Haodong 各 22.45%，合计 100.00%。矩阵原文件保留小组填写的技术分项、确认勾选、姓名和日期；此索引用于定位对应成果，不替代个人复核记录。

| 成员 | 总体比例 | 负责范围与对应已交付成果 | 文件与结果证据 | 配对复核 |
|---|---|---|---|---|
| Jiaqi Xie（25028285） | 27.55% | F1 产品验证与发布、共同 BPMN 建模、SD、需求追踪及小组协调；对应成果为可执行 F1、产品规则、SD 源文件和导出图、需求与模型追踪表。 | [F1 模型](../../models/operational/F1-Operational.bpmn)、[F1 规则](../../src/sprint2_demo/f1.py)、[SD/SR 源文件](../../models/istar/SD-SR.drawio)、[追踪表](traceability.md) | Jilong；实际复核日期、发现与结论待本人记录。 |
| Yunze Yu（25028284） | 27.55% | F2 库存与季节性可售状态、共同 BPMN 建模、SR、Camunda 配置和运行集成；对应成果为可执行 F2、库存规则、worker、持久化和演示启动入口。 | [F2 模型](../../models/operational/F2-Operational.bpmn)、[SR 图](../../models/istar/SR.svg)、[运行包](../../src/sprint2_runtime/README.txt)、[启动入口](../../Run-Sprint2.cmd) | Haodong；实际复核日期、发现与结论待本人记录。 |
| Jilong Cheng（25028281） | 22.45% | 与 Jiaqi 配对负责 F1 需求、表单、验收案例、测试及文档；对应成果包括产品提交和修改表单、F1 测试，以及缺失信息、修改和认证结果的场景证据。 | [提交表单](../../models/operational/forms/F1-Product-Details.form)、[修改表单](../../models/operational/forms/F1-Correct-Product-Details.form)、[F1 测试](../../tests/test_f1.py)、[运行验证](runtime-validation-2026-11-18.md) | Jiaqi；实际复核日期、发现与结论待本人记录。 |
| Haodong Yang（25061288） | 22.45% | 与 Yunze 配对负责 F2 需求、库存日期输入、边界数据、测试及文档；对应成果包括库存日期表单、F2 与运行测试，以及无效输入、库存耗尽和补货、重复订单、版本冲突和季节性路径证据。 | [库存日期表单](../../models/operational/forms/F2-Stock-and-Sale-Dates.form)、[F2 测试](../../tests/test_f2.py)、[运行测试](../../tests/test_sprint2_runtime.py)、[边界场景](../../review-evidence/runtime-2026-11-18/boundaries-engine.json) | Yunze；实际复核日期、发现与结论待本人记录。 |
| 合计 | 100.00% | 本轮总体分配。 |  |  |

共同交付的技术验证结果见 [11 月 18 日校验记录](evidence/implementation-check-2026-11-18.json)：58 项 Python 测试通过，七组真实引擎场景包含 45 项通过断言、40 个完成实例；另有人工 Tasklist 运行记录。认证使用本地示例数据，身份与确认订单由演示输入提供，季节性检查由显式调用触发。

上述成果路径用于核对负责范围，不单独证明某一成员亲自编写或运行了全部对应内容。个人独立运行、具体修改及配对复核仍须记录本人实际日期、输入、预期、输出和结论；现有共享测试不能替代个人记录。会议、确认勾选、签名和签字日期由四人据实完成，不预填导师批准。
