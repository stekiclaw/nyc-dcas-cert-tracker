# NYC DCAS Cert Tracker

基于 NYC DCAS 官方公开数据的候选人认证位置查询与追踪 Skill。支持不同考试和职位，不包含任何用户的个人数据。

## 功能

1. 查询当前 Cert Seq No 最小的机构，完整列出并列机构和认证批次。
2. 查询或持续追踪指定机构中的个人认证序号。
3. 列出最近一个日历月出现的全部机构、认证编号和个人序号。
4. 总结指定机构过去一年内各认证批次的序号变化。
5. 监测新增认证、覆盖范围、名单状态及到期日期变化；无实质变化不通知。

使用时会主动询问需要哪些功能。用户已明确选择时直接执行，定时运行不再提问。

## 安装和使用

将整个仓库作为 `nyc-dcas-cert-tracker` Skill 文件夹安装到支持 SKILL.md 的助手环境。Codex 可放在 `~/.codex/skills/nyc-dcas-cert-tracker/`；按当前宿主的 Skills 安装流程启用。

在对话中调用：

```text
$nyc-dcas-cert-tracker
查询我的当前最低认证序号、最近一个月的认证批次，以及某个机构过去一年的位置变化。
```

准备以下输入：

- First Name、Last Name，以及 MI（如有），按官方记录拼写。
- 考试编号和职位名称或 Title Code。
- 目标机构（机构查询和年度分析时需要）。
- 准确 List No（建议，用于排除同名）。

不需要提供 SSN、生日、住址或员工编号。

## Python 查询脚本

要求 Python 3.9+，使用标准库；不需要 GitHub、DCAS 或 Socrata API Key。宿主需允许访问 NYC Open Data。持续通知需要宿主提供可用的任务调度功能；运行脚本本身不会创建定时任务。

```bash
python scripts/dcas_cert.py person \
  --exam 4034 --title-code 13621 \
  --first YOUR_FIRST_NAME --last YOUR_LAST_NAME \
  --as-of 2026-10-10 --output person.json
```

按需加入 `--mi`、`--list-no`、`--agency-code`。全机构最低序号与月度查询不应加机构过滤。日期省略时默认使用纽约当天日期。

生成首次监测基线：

```bash
python scripts/dcas_cert.py monitor \
  --exam 4034 --title-code 13621 --output baseline.json
```

后续比较：

```bash
python scripts/dcas_cert.py monitor \
  --exam 4034 --title-code 13621 \
  --previous baseline.json --output current.json
```

查询成功后，由宿主保存新状态作为下一次的基线；不要在查询失败时覆盖最后一次成功记录。个人序号持续追踪需要宿主同时保存并比较 person 输出。快照、姓名和个人结果请放在仓库外，不要提交到 GitHub。

## 字段与解读

- `list_no`：考试名单号。
- `cert_issue_no`：认证编号；不同编号代表不同认证。
- `cert_seq_no`：候选人在该认证中的序号，不是实际聘用顺序或全局排名。
- `cert_date`：认证签发日期，区别于申请日期和考试名单建立日期。
- `cert_expiration_date`：认证到期日，区别于考试名单到期日。

“当前”默认按已签发、且到期日不早于查询日筛选；这不能证明行政有效性或个人任用资格。缺失到期日的记录单列为状态未知。不同批次的人数和筛选条件可能不同，年度序号差异不等于同一份名单中发生了晋升或候选人被聘用。

**名单认证、实际聘用、Permanent Appointment 必须分别确认。** 认证序号、人数、Provisional Replacement 标志和名单范围都不能单独证明 reachable、实际聘用或永久任用。名单号的最小/最大范围也不表示中间每个人均在认证中。

考试编号可能在不同年代重复使用，必须同时过滤 Title Code。例如 Computer Associate (Operations) 为考试 4034/04034、Title Code 13621。

## 官方来源

- [Civil Service List Certification](https://data.cityofnewyork.us/City-Government/Civil-Service-List-Certification/a9md-ynri)
- [Civil Service List (Active)](https://data.cityofnewyork.us/City-Government/Civil-Service-List-Active-/vx8i-nprf)

脚本核验分页完整性和数据更新状态。报告应分别注明查询日期、官方数据更新时间及认证事件日期。

## 文件

- `SKILL.md`：助手执行与主动提问流程。
- `scripts/dcas_cert.py`：官方查询和确定性计算。
- `references/data-and-reporting.md`：字段、日期规则和报表格式。
- `agents/openai.yaml`：Skill 界面元数据。
