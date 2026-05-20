"""
流程图推荐引擎
================
根据用户输入的文本/需求描述，智能推荐最适合的流程图建模方法。
基于 《流程图与建模方法知识手册》 中的 25 种方法构建知识库。

使用方法：
    python recommend.py "我想描述一下我的业务场景..."

或者直接运行后输入需求描述。
"""

import sys
import re
import io

# 确保 stdout 使用 UTF-8 编码，避免 Windows GBK 报错
if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ============================================================
# 知识库：每种方法的特征关键词、权重和元信息
# ============================================================

METHODS = [
    {
        "name": "IDEF0（功能建模图）",
        "category": "业务与流程建模",
        "stage": "战略层 — 宏观规划与诊断",
        "summary": "界定业务边界与控制规则",
        "keywords": {
            "业务边界": 10, "控制规则": 10, "制度约束": 9, "职能规划": 8,
            "资源支持": 7, "立项": 7, "大框架": 8, "顶层规划": 8,
            "宏观规划": 8, "集团高层": 7, "战略": 5, "边界": 5, "管控": 6,
            "icomas": 10, "icam": 8, "idef0": 20, "idef": 15,
        },
        "why": "IDEF0 专注于从宏观层面界定业务的边界与控制规则，适合在项目立项之初搭建高层级的业务职能框架。"
    },
    {
        "name": "VSM（价值流图）",
        "category": "业务与流程建模",
        "stage": "战略层 — 宏观规划与诊断",
        "summary": "诊断流程效率瓶颈",
        "keywords": {
            "效率瓶颈": 10, "时间浪费": 10, "精益管理": 10, "提效": 9,
            "缩短周期": 8, "交付周期": 8, "物流": 7, "信息流": 7,
            "价值流": 15, "浪费": 8, "瓶颈": 8, "流程优化": 6,
            "精益": 10, "vsm": 20, "价值流图": 20, "节拍": 7, "周期时间": 7,
        },
        "why": "VSM（价值流图）专门用于诊断流程中的效率瓶颈和时间浪费，适合精益管理和业务提效诊断项目。"
    },
    {
        "name": "CFF（跨功能流程图 / 泳道图）",
        "category": "业务与流程建模",
        "stage": "执行层 — 中观组织与逻辑",
        "summary": "划分跨部门职责与流转顺序",
        "keywords": {
            "跨部门": 10, "职责划分": 9, "泳道": 15, "sop": 10,
            "标准作业": 8, "流转顺序": 9, "谁做什么": 9, "部门协作": 8,
            "角色": 7, "岗位": 7, "协同": 7, "灰色地带": 7,
            "跨职能": 10, "责任": 6, "流程步骤": 5, "cff": 15,
            "swimlane": 15, "泳道图": 20,
        },
        "why": "CFF（泳道图）通过横向或纵向的泳道明确划分不同部门/角色的职责和流转顺序，适合梳理跨部门协同流程和编写 SOP。"
    },
    {
        "name": "EPC（事件驱动过程链）",
        "category": "业务与流程建模",
        "stage": "执行层 — 中观组织与逻辑",
        "summary": "梳理状态与动作的因果逻辑",
        "keywords": {
            "事件驱动": 10, "因果逻辑": 10, "状态与动作": 10,
            "触发条件": 9, "sap": 10, "erp": 8, "信息化规划": 8,
            "事件": 5, "条件": 5, "结果": 5, "闭环": 7,
            "epc": 20, "事件驱动过程链": 20, "sap实施": 10,
            "业务流程建模": 5, "erp系统": 8,
        },
        "why": "EPC 通过事件与功能的严格交替，梳理状态与动作之间的强因果逻辑，适合大型传统企业信息化规划或 SAP/ERP 实施。"
    },
    {
        "name": "BPMN 2.0（业务流程建模与标注）",
        "category": "业务与流程建模",
        "stage": "技术前置层 — 微观落地与IT准备",
        "summary": "工业级流程精确建模（可执行）",
        "keywords": {
            "工作流引擎": 10, "可执行": 8, "camunda": 15, "flowable": 15,
            "审批流": 9, "异常处理": 8, "超时催办": 8, "bpm": 10,
            "系统自动": 7, "自动化流程": 8, "网关": 7, "事件圈": 6,
            "bpmn": 20, "bpmn2": 20, "流程引擎": 10,
            "工作流": 8, "activiti": 10,
        },
        "why": "BPMN 2.0 使用工业级标准语法精确定义系统对业务流的代码级控制逻辑，适合把流程配置到工作流引擎中自动跑审批。"
    },
    {
        "name": "DFD（数据流图）",
        "category": "业务与流程建模",
        "stage": "技术前置层 — 微观落地与IT准备",
        "summary": "分析系统数据流转与存储",
        "keywords": {
            "数据流": 10, "数据存储": 9, "数据加工": 9, "数据库设计": 8,
            "表结构": 7, "外部实体": 8, "系统接口": 7, "etl": 7,
            "数据搬运": 8, "数据结构": 6, "数据流向": 8,
            "dfd": 20, "数据流图": 20, "数据建模": 5,
        },
        "why": "DFD 剥离人和组织架构，纯粹从数据视角分析系统内部数据的流转、加工和存储，适合在设计数据库和系统接口前使用。"
    },
    {
        "name": "类图（Class Diagram）",
        "category": "UML",
        "stage": "结构层 — 静态结构设计",
        "summary": "定义类的静态结构与关系",
        "keywords": {
            "类": 8, "属性": 8, "方法": 8, "继承": 8, "接口": 6,
            "面向对象": 8, "实体关系": 7, "orm": 6, "数据库表": 5,
            "类关系": 8, "泛化": 7, "依赖": 6, "关联": 6,
            "class diagram": 15, "类图": 20, "uml类图": 15,
            "对象模型": 7,
        },
        "why": "类图用三段式矩形框展现系统的类、属性、方法及其关系，是面向对象编程的基础骨架，适合详细设计阶段指导编码。"
    },
    {
        "name": "对象图（Object Diagram）",
        "category": "UML",
        "stage": "结构层 — 静态结构设计",
        "summary": "展示运行时对象快照",
        "keywords": {
            "对象快照": 10, "运行时": 8, "实例化": 8, "具体对象": 8,
            "内存状态": 7, "运行瞬间": 7, "实例": 6,
            "对象图": 20, "object diagram": 15, "特定时刻": 7,
        },
        "why": "对象图是类图的运行快照，展示系统在某一瞬间对象被实例化后的真实数据状态，适合分析复杂类关系在运行时的具体表现。"
    },
    {
        "name": "包图（Package Diagram）",
        "category": "UML",
        "stage": "结构层 — 静态结构设计",
        "summary": "规划模块化代码目录结构",
        "keywords": {
            "模块划分": 10, "目录结构": 9, "解耦": 8, "包管理": 8,
            "命名空间": 7, "依赖管理": 8, "模块化": 8, "子系统": 7,
            "包图": 20, "package diagram": 15, "代码组织": 7,
            "组件划分": 6,
        },
        "why": "包图把成百上千个类按功能打包成模块，展示模块间的依赖和可见性，适合系统设计初期划分代码目录结构。"
    },
    {
        "name": "用例图（Use Case Diagram）",
        "category": "UML",
        "stage": "动态层 — 动态行为与运行交互设计",
        "summary": "明确系统功能边界与用户需求",
        "keywords": {
            "需求分析": 9, "用户视角": 8, "功能边界": 8, "actor": 10,
            "角色": 7, "系统功能": 7, "需求": 5, "用户需求": 7,
            "usecase": 15, "用例图": 20, "用例": 8,
            "use case": 15, "业务范围": 7,
        },
        "why": "用例图从用户视角出发展示系统能提供的功能，适合需求分析阶段用来界定系统边界，明确谁能用系统做什么。"
    },
    {
        "name": "活动图（Activity Diagram）",
        "category": "UML",
        "stage": "动态层 — 动态行为与运行交互设计",
        "summary": "表达算法逻辑或操作路径",
        "keywords": {
            "算法逻辑": 9, "操作路径": 8, "并发": 8, "分支": 7,
            "登录流程": 8, "验证流程": 7, "传统流程图": 7,
            "业务逻辑": 6, "判断": 6, "流程": 5,
            "activity diagram": 15, "活动图": 20, "uml活动图": 12,
        },
        "why": "活动图是最接近传统流程图的 UML 图，原生支持并发和分支，适合表达复杂算法逻辑或用户在系统里的具体操作路径。"
    },
    {
        "name": "时序图 / 顺序图（Sequence Diagram）",
        "category": "UML",
        "stage": "动态层 — 动态行为与运行交互设计",
        "summary": "展示对象间按时间顺序的消息交互",
        "keywords": {
            "消息交互": 10, "时间顺序": 9, "接口调用": 9, "api": 7,
            "前端后端": 8, "通信": 7, "请求响应": 7, "调用链": 8,
            "消息传递": 7, "交互流程": 7,
            "sequence diagram": 15, "时序图": 20, "顺序图": 15,
            "交互图": 7,
        },
        "why": "时序图按时间先后展示不同对象/子系统之间如何互发消息和调用接口，研发最常用，适合设计具体的系统交互流程。"
    },
    {
        "name": "状态机图（State Machine Diagram）",
        "category": "UML",
        "stage": "动态层 — 动态行为与运行交互设计",
        "summary": "管理对象生命周期的状态流转",
        "keywords": {
            "状态流转": 10, "生命周期": 9, "订单状态": 9,
            "状态变化": 9, "触发事件": 8, "状态机": 10,
            "状态迁移": 9, "待付款": 7, "已发货": 7,
            "state machine": 15, "状态机图": 20, "状态图": 12,
        },
        "why": "状态机图专注于一个特定对象在生命周期里的状态变化以及触发变化的条件，适合规范电商订单状态等复杂状态模型。"
    },
    {
        "name": "组件图 / 构件图（Component Diagram）",
        "category": "UML",
        "stage": "物理层 — 组件契约与网络拓扑设计",
        "summary": "定义软件模块间的接口契约",
        "keywords": {
            "接口契约": 10, "微服务": 8, "dll": 8, "jar": 8,
            "组件依赖": 8, "服务接口": 7, "前后端分离": 7,
            "软件模块": 7, "可执行文件": 6,
            "component diagram": 15, "组件图": 20, "构件图": 15,
        },
        "why": "组件图展示软件系统的物理构建块及其接口契约与依赖关系，适合微服务架构或前后端分离中定义服务接口边界。"
    },
    {
        "name": "部署图（Deployment Diagram）",
        "category": "UML",
        "stage": "物理层 — 组件契约与网络拓扑设计",
        "summary": "规划物理硬件与网络拓扑",
        "keywords": {
            "部署": 9, "服务器": 8, "网络拓扑": 9, "集群": 8,
            "负载均衡": 8, "硬件": 7, "运维": 7, "虚拟机": 7,
            "云主机": 7, "物理架构": 7,
            "deployment diagram": 15, "部署图": 20, "节点": 6,
        },
        "why": "部署图使用三维立方体代表物理节点，描述软件系统的物理拓扑架构，适合在上线前规划服务器集群和网络配置。"
    },
    {
        "name": "Context Diagram（系统上下文图）",
        "category": "C4 模型",
        "stage": "项目启动 — 宏观",
        "summary": "展示系统生态边界（宏观）",
        "keywords": {
            "系统生态": 9, "宏观": 7, "外部系统": 8, "整体架构": 7,
            "业务方": 7, "项目启动": 8, "系统边界": 8,
            "context diagram": 20, "系统上下文": 15, "语境图": 10,
            "c4上下文": 15, "生态边界": 8,
        },
        "why": "Context Diagram 是 C4 模型的顶层视图，不讲技术细节，纯粹展示系统与周边人和外部系统的互动，适合项目启动时向非技术角色介绍。"
    },
    {
        "name": "Container Diagram（容器图）",
        "category": "C4 模型",
        "stage": "架构中期 — 技术选型与部署",
        "summary": "展示技术选型与部署单元",
        "keywords": {
            "技术选型": 9, "容器": 7, "部署单元": 8, "springboot": 7,
            "前后端架构": 7, "technology stack": 7, "http": 6,
            "grpc": 7, "技术架构": 7,
            "container diagram": 20, "容器图": 15, "c4容器": 12,
        },
        "why": "Container Diagram 将系统拆分成多个独立的技术容器，标注技术栈和通信协议，适合架构中期明确技术选型和部署边界。"
    },
    {
        "name": "Component Diagram（组件图 - C4）",
        "category": "C4 模型",
        "stage": "详细设计 — 容器内部",
        "summary": "展示容器内部模块结构",
        "keywords": {
            "容器内部": 10, "代码组件": 9, "模块化结构": 8,
            "控制器": 6, "服务层": 7, "数据访问": 7,
            "c4组件": 12, "c4 component": 15,
        },
        "why": "C4 的 Component Diagram 聚焦在某个具体容器内部，将其拆解为代码组件并标注依赖关系，适合详细设计阶段指导模块开发。"
    },
    {
        "name": "Code Diagram（代码图 - C4）",
        "category": "C4 模型",
        "stage": "极少数情况 — 代码级",
        "summary": "展示代码级别实现结构",
        "keywords": {
            "代码实现": 8, "类结构": 7, "ide自动生成": 7,
            "设计模式": 6, "代码级": 7,
            "code diagram": 20, "c4代码": 12,
        },
        "why": "C4 的 Code Diagram 放大到代码级别，通常展现为 UML 类图或 ERD，用于极少数复杂算法或关键设计模式的落地说明。"
    },
    {
        "name": "Strategy & Motivation View（战略与动机视角）",
        "category": "ArchiMate",
        "stage": "立项规划",
        "summary": "对齐战略目标与系统需求",
        "keywords": {
            "战略目标": 10, "商业价值": 9, "投资回报": 9,
            "数字化转型": 9, "高管汇报": 8, "立项": 8,
            "archimate战略": 15, "archimate motivation": 15,
            "战略驱动": 8, "archimate": 10,
        },
        "why": "Strategy & Motivation View 回答企业为什么做数字化转型，将高层战略目标与系统需求挂钩，适合向高管汇报技术投资的商业价值。"
    },
    {
        "name": "Business Process Cooperation View（业务流程协作视角）",
        "category": "ArchiMate",
        "stage": "业务架构",
        "summary": "企业级业务流程全局梳理",
        "keywords": {
            "业务线": 8, "全局业务": 8, "企业架构": 7,
            "业务部门配合": 8, "业务梳理": 7,
            "archimate业务": 12, "业务协作": 8,
        },
        "why": "Business Process Cooperation View 从宏观展示企业各部门/业务线间的流程配合，比传统流程图更高维，适合企业全局业务梳理。"
    },
    {
        "name": "Application Cooperation View（应用协作视角）",
        "category": "ArchiMate",
        "stage": "IT 架构",
        "summary": "系统间集成与数据流向规划",
        "keywords": {
            "系统集成": 9, "数据打通": 8, "erp": 7, "crm": 7,
            "wms": 7, "接口": 6, "系统间": 8, "集成规划": 8,
            "archimate应用": 12, "应用协作": 8,
        },
        "why": "Application Cooperation View 描述企业内部所有管理系统间的协作与数据流向，适合 IT 架构师做信息系统集成规划。"
    },
    {
        "name": "Layered View（分层架构视角）",
        "category": "ArchiMate",
        "stage": "全局蓝图",
        "summary": "技术→应用→业务的完整映射",
        "keywords": {
            "分层架构": 9, "全局映射": 8, "业务层": 7, "应用层": 7,
            "技术层": 7, "蓝图": 8, "数字化蓝图": 8,
            "archimate分层": 12, "分层视图": 8,
        },
        "why": "Layered View 是 ArchiMate 的核心视图，将业务层、应用层、技术层纵向堆叠，一眼看清从底层服务器到应用系统再到业务流程的完整链条。"
    },
    {
        "name": "Infrastructure / Technology View（技术与基础设施视角）",
        "category": "ArchiMate",
        "stage": "运维安全",
        "summary": "基础设施与运维拓扑规划",
        "keywords": {
            "基础设施": 9, "灾备": 9, "机房": 8, "云资源": 8,
            "网络规划": 7, "运维": 7, "中间件": 6, "系统软件": 6,
            "archimate技术": 12, "archimate infrastructure": 12,
        },
        "why": "Infrastructure / Technology View 描述支撑企业运行的物理和软件基础设施拓扑，适合运维架构师做机房、云资源和灾备规划。"
    },
    {
        "name": "Implementation & Migration View（实施与演进视角）",
        "category": "ArchiMate",
        "stage": "项目管理",
        "summary": "演进路线与实施计划",
        "keywords": {
            "路线图": 9, "实施计划": 9, "分期上线": 8,
            "演进": 7, "pmo": 8, "项目群": 8, "roadmap": 9,
            "archimate实施": 12, "archimate migration": 12,
        },
        "why": "Implementation & Migration View 解决系统如何落地的问题，将企业架构拆解为多期项目并展示演进路线，适合 PMO 规划系统上线路线图。"
    },
]

# 额外加权短语（精准匹配）
PHRASE_MAP = [
    # (正则表达式, 方法索引, 加分)
    (r"我不确定该用哪种流程图", -1),  # 触发通用引导
    (r"帮我推荐.*(?:图|方法|工具)", -1),
    (r"什么图.*适合|适合.*什么图|用哪种图|推荐.*流程", -1),
    (r"业务流程.*梳理|梳理.*业务流程", 2),  # CFF
    (r"订单.*状态|状态.*订单", 12),  # 状态机图
    (r"登录|注册|认证.*流程", 10),  # 活动图
    (r"支付.*流程|支付.*交互", 11),  # 时序图
    (r"审批.*流程|流程.*审批", 4),  # BPMN
    (r"数据库.*设计|设计.*数据表|表结构", 5),  # DFD
    (r"类.*设计|设计.*类", 6),  # 类图
    (r"微服务", 13),  # 组件图
    (r"微服务.*架构|架构.*微服务", 13),  # 组件图（增强）
    (r"系统.*部署|部署.*架构", 14),  # 部署图
    (r"需求.*分析|分析.*需求|功能.*需求", 9),  # 用例图
    (r"技术.*选型|选型.*技术", 16),  # Container Diagram
    (r"战略.*规划|规划.*战略|数字化转型", 19),  # Strategy & Motivation
    (r"效率.*低|提高.*效率|优化.*流程|瓶颈", 1),  # VSM
    (r"sop|标准.*流程|标准.*作业", 2),  # CFF
    (r"状态机|状态.*流转|状态.*变化", 12),  # 状态机图
    (r"并发|并行.*处理|多线程", 10),  # 活动图
    (r"接口.*调用|调用.*接口|api.*交互", 11),  # 时序图
    (r"erp|sap.*实施", 3),  # EPC
    (r"模块.*划分|划分.*模块|解耦", 8),  # 包图
    (r"er图|实体.*关系|er模型", 6),  # 类图
    (r"系统.*集成|集成.*系统|打通.*系统", 21),  # Application Cooperation
    (r"蓝图|全局.*架构|整体.*架构", 22),  # Layered View
    (r"灾备|高可用|机房|服务器.*规划", 23),  # Infrastructure
    (r"路线图|roadmap|实施.*计划|分期.*上线", 24),  # Implementation & Migration
    (r"立项|投资.*回报|商业.*价值", 19),  # Strategy & Motivation
    (r"产品经理|业务方|客户.*需求|非技术", 15),  # Context Diagram
    (r"运行.*快照|特定.*时刻|内存.*状态", 7),  # 对象图
    (r"代码.*实现|代码.*结构|设计.*模式", 18),  # Code Diagram
    (r"工作流|bpm|流程.*自动化|自动.*审批", 4),  # BPMN 2.0
    (r"跨部门|部门.*协作|协同.*效率", 2),  # CFF
    (r"边界.*控制|控制.*规则|制度.*约束", 0),  # IDEF0
    (r"事件.*驱动|触发.*条件|条件.*触发", 3),  # EPC
    (r"消息.*队列|消息.*交互|通信.*流程", 11),  # 时序图
    (r"容器.*内部|代码.*组件|模块.*依赖", 17),  # C4 Component
    (r"系统.*上下文|生态.*边界|外部.*系统", 15),  # Context Diagram
    (r"前后端.*分离|前端.*后端.*交互", 11),  # 时序图
    (r"物理.*拓扑|网络.*拓扑|服务器.*集群", 14),  # 部署图
    (r"高频.*调用|调用.*链路|接口.*调用链", 11),  # 时序图
    (r"项目群|pmo|多期.*项目|分期.*实施", 24),  # Implementation
    (r"遗留.*系统|改造|升级.*系统", 21),  # Application Cooperation
    (r"职责.*不明|分工.*不清|责任.*划分", 2),  # CFF
    (r"框架.*规划|顶层.*设计|集团.*规划", 0),  # IDEF0
    (r"camunda|flowable|activiti|流程引擎", 4),  # BPMN
    (r"生命周期|状态.*管理|审核.*状态|审批.*状态", 12),  # 状态机图
    (r"数据.*流转|数据.*流向|数据处理", 5),  # DFD
    (r"技术.*架构|应用.*架构|业务.*架构.*分层", 22),  # Layered View
    (r"讲解.*架构|介绍.*系统|团队.*新人", 15),  # Context Diagram

    # === 新增增强短语 ===
    (r"完整映射|技术.*业务.*支撑|底层.*上层|自下而上", 22),  # Layered View 增强
    (r"业务.*技术.*映射|基础设施.*业务|服务器.*业务", 22),  # Layered View 增强
    (r"企业架构.*设计|企业架构.*规划|企业级.*架构", 20),  # Business Process Cooperation
    (r"逐级放大|由远及近|不同角色.*理解", 15),  # Context Diagram
    (r"数据.*加工|数据.*处理.*流程", 5),  # DFD 增强
    (r"业务流程.*优化|流程.*效率|流程.*改进", 1),  # VSM 增强
    (r"系统.*交互|对象.*通信|组件.*通信", 11),  # 时序图 增强
    (r"状态.*迁移.*图|状态.*转换|流程.*状态", 12),  # 状态机图 增强
    (r"业务.*规则|规则.*引擎|决策.*流程", 3),  # EPC 增强
    (r"前端.*组件|组件.*复用|组件.*依赖", 13),  # UML组件图 增强
    (r"代码.*生成|自动.*生成.*代码|逆向.*工程", 18),  # Code Diagram
    (r"多期.*实施|演进.*路线|分期.*建设", 24),  # Implementation & Migration
    (r"系统.*运维|运维.*架构|监控.*部署", 23),  # Infrastructure
    (r"技术选型.*架构|技术栈.*设计|框架.*选型", 16),  # Container Diagram
    (r"用户.*故事|用户.*场景|功能.*列表", 9),  # 用例图 增强
    (r"包.*依赖|模块.*组织|代码.*目录", 8),  # 包图 增强
    (r"继承.*关系|关联.*关系|聚合.*组合", 6),  # 类图 增强
    (r"运行.*实例|对象.*实例|实例.*关系", 7),  # 对象图 增强
    (r"业务.*事件|事件.*流程|事件.*触发", 3),  # EPC 增强
    (r"跨.*系统|系统.*交互.*数据|数据.*交换", 21),  # Application Cooperation
    (r"项目.*规划|实施.*路线|上线.*计划", 24),  # Implementation & Migration
    (r"系统.*边界|子系统.*划分|范围.*界定", 0),  # IDEF0 增强
    (r"物流.*流程|供应.*链|交付.*流程", 1),  # VSM 增强
    (r"用户.*权限|权限.*管理|角色.*权限", 9),  # 用例图
    (r"订单.*数据|订单.*信息.*流转", 5),  # DFD
]


def tokenize(text: str) -> str:
    """预处理文本：小写、去标点"""
    text = text.lower()
    text = re.sub(r'[^\w一-鿿\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def score_methods(description: str) -> list:
    """对每种方法打分，返回 (得分, 方法字典) 列表"""
    raw = description
    text = tokenize(description)
    scores = []

    for i, method in enumerate(METHODS):
        score = 0
        matched_keywords = []

        # 1. 关键词匹配
        for keyword, weight in method["keywords"].items():
            if keyword.lower() in text:
                score += weight
                matched_keywords.append(keyword)

        # 2. 短语正则匹配（精准匹配，权重高）
        for pattern, target in PHRASE_MAP:
            if target == i and re.search(pattern, raw):
                score += 15
                matched_keywords.append(f"[短语] {pattern}")

        # 3. 方法名直接命中加分
        method_name = method["name"].lower()
        name_parts = [p.strip() for p in re.split(r'[（(）)]', method_name) if p.strip()]
        for part in name_parts:
            if len(part) > 1 and part in text:
                score += 25

        scores.append((score, matched_keywords, method))

    # 按得分排序
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores


def format_recommendation(scores: list, top_n: int = 3):
    """格式化推荐结果"""
    top_scores = [s for s in scores if s[0] > 0]

    if not top_scores:
        return (
            "😅 根据您的描述，我没有找到高度匹配的流程图方法。\n\n"
            "建议您描述得更加具体一些，例如：\n"
            "- 您想梳理什么业务流程？\n"
            "- 涉及哪些部门或角色？\n"
            "- 是面向业务还是面向技术实现？\n"
            "- 您当前处于项目的什么阶段？"
        )

    result_parts = []
    result_parts.append("## 推荐结果\n")

    for rank, (score, keywords, method) in enumerate(top_scores[:top_n], 1):
        if rank == 1:
            badge = "🥇 强烈推荐"
        elif rank == 2:
            badge = "🥈 备选推荐"
        else:
            badge = "🥉 也可考虑"

        bar_len = min(score // 5, 20)
        score_bar = "█" * bar_len + "░" * (20 - bar_len)

        result_parts.append(f"### {badge}：{method['name']}\n")
        result_parts.append(f"**类别**：{method['category']} ｜ **阶段**：{method['stage']}\n")
        result_parts.append(f"**一句话**：{method['summary']}\n")
        result_parts.append(f"**匹配度**：{score_bar} ({score}分)\n")
        result_parts.append(f"**原因**：{method['why']}\n")

        if keywords:
            result_parts.append(f"> 匹配关键词：{'、'.join(keywords[:8])}\n")

        result_parts.append("")

    return "\n".join(result_parts)


def recommend(description: str):
    """主推荐函数"""
    print("\n" + "=" * 60)
    print("  流程图推荐引擎")
    print("=" * 60)
    print(f"\n📝 您的需求描述：{description}\n")
    print("─" * 60)

    scores = score_methods(description)
    result = format_recommendation(scores)
    print(result)

    print("─" * 60)
    print("\n💡 提示：如果推荐不够准确，请尝试更详细地描述您的场景、目标和当前阶段。")
    print("=" * 60)


def interactive_mode():
    """交互式模式"""
    print("\n" + "=" * 60)
    print("  🔍 流程图推荐引擎（交互模式）")
    print("=" * 60)
    print("请输入您的需求描述，我将为您推荐最适合的流程图方法。")
    print("输入 'q' 退出，输入 'list' 查看所有方法。\n")

    while True:
        try:
            text = input(">> ").strip()
            if not text:
                continue
            if text.lower() == 'q':
                print("再见！")
                break
            if text.lower() == 'list':
                print("\n知识库包含以下 25 种方法：\n")
                cats = {}
                for m in METHODS:
                    cats.setdefault(m["category"], []).append(m["name"])
                for cat, names in cats.items():
                    print(f"  📂 {cat}")
                    for n in names:
                        print(f"     • {n}")
                print()
                continue

            scores = score_methods(text)
            result = format_recommendation(scores)
            print("\n" + result)
            print("─" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误：{e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        description = " ".join(sys.argv[1:])
        recommend(description)
    else:
        interactive_mode()
