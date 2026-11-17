# Sprint 2 真实运行验证 — 2026 年 11 月 18 日

本机 Camunda Run **8.10.9** 已部署两份可执行 BPMN 和三张 Form。以下七组场景共完成 **40 个流程实例**，**45 项断言全部通过**；记录中的实例均为 COMPLETED，且没有 incident。

| 场景 | 实际核查结果 | 断言数 / 完成实例数 | 证据 |
|---|---|---:|---|
| happy | 产品发布，然后库存 10 → 6；可售投影与新版本一致 | 3 / 4 | [JSON](../../review-evidence/runtime-2026-11-18/happy-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/happy-worker.log) |
| correction | 产品名称缺失 → 补正任务 → 重新提交并验证 → 发布；补正前未发布 | 6 / 4 | [JSON](../../review-evidence/runtime-2026-11-18/correction-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/correction-worker.log) |
| organic | 有效的模拟有机认证 → 发布 | 3 / 4 | [JSON](../../review-evidence/runtime-2026-11-18/organic-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/organic-worker.log) |
| pending | 模拟认证服务不可用 → 不发布并保存后续处理记录 | 2 / 2 | [JSON](../../review-evidence/runtime-2026-11-18/pending-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/pending-worker.log) |
| invalid-certificate | 模拟认证无效 → 补正为有效认证 → 再次验证后发布 | 7 / 4 | [JSON](../../review-evidence/runtime-2026-11-18/invalid-certificate-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/invalid-certificate-worker.log) |
| invalid-input | 负库存、小数库存、日期颠倒 → 拒绝；库存、版本、投影不变 | 15 / 10 | [JSON](../../review-evidence/runtime-2026-11-18/invalid-input-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/invalid-input-worker.log) |
| boundaries | 库存耗尽、重复订单、版本冲突、补货和销售期外状态 | 9 / 12 | [JSON](../../review-evidence/runtime-2026-11-18/boundaries-engine.json) / [worker log](../../review-evidence/runtime-2026-11-18/boundaries-worker.log) |

JSON 包含实际 instance keys、完成任务和业务操作结果，以及库存、版本、客户可售投影的前后快照。自动场景通过 REST 完成真实人工任务，继续使用真实引擎、消息和 worker。它们不代表人工逐项操作网页表单。

另外完成了两次人工 Tasklist 正常路径：[界面验证运行](../../review-evidence/runtime-2026-11-18/tasklist-ui-run.json)和[后续完整运行](../../review-evidence/runtime-2026-11-18/tasklist-user-run.json)。两次均为 F1 发布后 F2 库存 10 → 6、版本 0 → 1，四个相关实例完成。启动器不自动完成这些人工任务。

## 人工演示

在配置好的 Windows 电脑上双击仓库根目录的 Run-Sprint2.cmd，保持窗口打开。Tasklist/Operate 地址为 http://localhost:8080，开发环境账号为 demo / demo。

F1：Submit product details → Assign to me → 展示数量10与销售日期 → Complete Task。
F2：Enter stock and sale dates → Assign to me → New quantity改为6 → Complete Task。
随后展示 Operate 完成实例，以及控制台或 work/manual-demo-latest.json 中的库存和版本。

## 重跑七组验证

先启动本地引擎；从仓库根目录的 PowerShell 运行：

```powershell
$env:PYTHONPATH = 'src'
$env:CAMUNDA_REST_URL = 'http://127.0.0.1:8080/v2'
python -m sprint2_runtime deploy
python -m sprint2_runtime demo --date 2026-11-18 --scenario happy
python -m sprint2_runtime demo --date 2026-11-18 --scenario correction
python -m sprint2_runtime demo --date 2026-11-18 --scenario organic
python -m sprint2_runtime demo --date 2026-11-18 --scenario pending
python -m sprint2_runtime demo --date 2026-11-18 --scenario invalid-certificate
python -m sprint2_runtime demo --date 2026-11-18 --scenario invalid-input
python -m sprint2_runtime demo --date 2026-11-18 --scenario boundaries
```

每条 demo 命令包含自己的 worker，不需同时开另一个 worker。数据库默认位于 work/sprint2-runtime.sqlite3，须与对应引擎数据一起保留；这些命令会建立新的演示实例与产品。JSON 写入 stdout，worker日志写入 stderr。过期季节场景显式采用销售结束日之后的业务日期，不依赖电脑系统日期。

本地复核与记录完整性检查：python tools/verify_sprint2_delivery.py。该命令重跑模型检查及测试，并验证已保存的引擎证据；不会再次创建引擎实例。

## 本轮复核和限制

[模型复核](model-review-2026-11-18.md)检查了 SD/SR、战略和操作模型的对应关系，以及老师指出的责任池/泳道归属。未发现需要改动业务图结构的问题。更新了旧的临时来源路径和过时进度说明。

无效输入测试直接提交 REST，是为了证明即使绕过浏览器校验，服务仍会拒绝负库存、小数和倒置日期。正常手工路径单独验证网页表单。

认证使用 DEMO-VALID、DEMO-INVALID、DEMO-UNAVAILABLE 本地响应，不连接真实认证机构。身份和订单确认是演示输入。季节变更通过命令触发；没有自动定时器。SQLite 和客户可售投影为本机实现。初始产品/来源/所有者错误仍可能在 F2_Load 引发 incident；生产鉴权、真实支付、外部集成与完整恢复属于后续工作。

本记录不替代个人贡献、组员复核、视频录制或 Blackboard 提交回执。云端图和本地可执行文件分别保存。
