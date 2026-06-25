# 毛利规则文档目录

将订单毛利、抽成、司机收入、补贴、优惠、渠道成本和结算口径文档放在此目录下。

## 支持的格式

- Markdown (`.md`) - 推荐
- PDF (`.pdf`)
- Word (`.docx`)
- 纯文本 (`.txt`)

## 文件命名规范

格式：`{rule_id}_{rule_name}.{ext}`

示例：

- `P001_订单毛利链路分析口径.md`
- `P002_司机收入结算异常识别.md`

## 导入命令

```bash
python -m ingestion.ingest --source data/profit --scene profit
```
