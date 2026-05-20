---
name: recommend-flowchart
description: 根据用户输入的文本/需求描述，智能推荐最适合的流程图建模方法（支持 25 种方法），并给出推荐理由
---

# /recommend-flowchart

根据业务需求或问题描述，智能推荐最适合的流程图或建模方法。

## Usage

```
/recommend-flowchart 你的需求描述...
```

例如：

```
/recommend-flowchart 我想梳理跨部门审批流程，涉及销售部和财务部
/recommend-flowchart 需要设计数据库表结构，分析订单数据如何流转
/recommend-flowchart 公司要做微服务改造，定义服务接口边界
/recommend-flowchart 电商订单状态从下单到签收的流转
/recommend-flowchart 向董事会汇报数字化转型的技术投资价值
```

## How It Works

1. 读取用户输入的描述文本
2. 通过关键词加权匹配 + 精准短语正则匹配，对 25 种方法进行打分
3. 返回 Top 3 推荐结果，包含匹配度、推荐理由和匹配关键词
4. 如果输入不相关，引导用户更具体地描述

## Supported Methods (25种)

- **业务与流程建模**：IDEF0、VSM、CFF（泳道图）、EPC、BPMN 2.0、DFD
- **UML**：类图、对象图、包图、用例图、活动图、时序图、状态机图、组件图、部署图
- **C4 模型**：Context Diagram、Container Diagram、Component Diagram、Code Diagram
- **ArchiMate**：Strategy & Motivation、Business Process Cooperation、Application Cooperation、Layered View、Infrastructure/Technology View、Implementation & Migration View

## 输出示例

```
🥇 强烈推荐：CFF（跨功能流程图 / 泳道图）
**类别**：业务与流程建模 ｜ **阶段**：执行层 — 中观组织与逻辑
**匹配度**：█████████░░░░░░░░░░░ (47分)
**原因**：CFF（泳道图）通过横向或纵向的泳道明确划分...
> 匹配关键词：跨部门、职责划分、SOP
```
