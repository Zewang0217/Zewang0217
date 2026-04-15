<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=Hi%20there,%20I'm%20Zewang%20!&fontSize=50&animation=fadeIn&fontAlignY=38&desc=Java%20/%20AI%20Backend%20Developer%20&descAlignY=61&descAlign=62" />

  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=500&size=24&pause=1000&color=2563EB&center=true&vCenter=true&width=500&lines=👨‍🎓+Student+at+ECNU;💻+Java+%26+Spring+Boot+Developer;🤖+AI+Agent+Explorer" alt="Typing SVG" />
</div>

## 👨‍💻 关于我 (About Me)

你好！我是 **Zewang ( gaoxinghao)**，目前就读于**华东师范大学 (ECNU) 软件工程专业**(大二)。我对底层技术架构和前沿的 AI 应用充满热情，专注于 Java 高并发后端开发以及基于大模型的多智能体 (Multi-Agent) 系统落地。

- 🔭 **求职状态：** 正在寻找 **Java 后端开发 / AI 应用研发** 的实习机会。
- 🌱 **当前专注：** 大模型的 GUI Agent / 多智能体协作架构 / LLM 的实际应用
- 💡 **技术理念：** 坚信“技术服务于业务”，热衷于使用优雅的代码和现代化的技术栈解决复杂的系统级问题, 熟练使用大模型辅助完成代码.
- 📫 **联系方式：** Zewang0217@outlook.com
- 📝 **个人博客：** https://zewang0217.github.io/
 
---

## 🛠️ 核心技术栈 (Tech Stack)

### 💻 后端开发与架构 (Backend)
![Java](https://img.shields.io/badge/Java_21-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring_Boot_3-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white)
![MyBatis](https://img.shields.io/badge/MyBatis_Plus-000000?style=for-the-badge&logo=mybatis&logoColor=white)

### 🗄️ 数据库与中间件 (Database & Middleware)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka_%26_Streams-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)

### 🤖 AI 与大模型应用 (AI & LLM)
![LangChain](https://img.shields.io/badge/LangChain4j-121212?style=for-the-badge&logo=chainlink&logoColor=white)
![Milvus](https://img.shields.io/badge/Milvus_Vector_DB-0D94E6?style=for-the-badge&logo=milvus&logoColor=white)
![Prompt Engineering](https://img.shields.io/badge/Agent_%26_RPA-FF9900?style=for-the-badge&logo=openai&logoColor=white)

---

## 🚀 核心开源项目 (Featured Projects)

这里是我在**高并发架构**与 **AI Agent 落地**领域的深度实践：

### 🎮 [AI 剧本杀 (AI-Jubensha) —— 沉浸式多智能体推理平台](https://github.com/Zewang0217/ai-jubensha)
这是一个高度复杂的 AI 驱动项目，将大语言模型与剧本杀游戏深度结合。不仅实现了流式剧本生成，还构建了多个拥有独立人格和推理能力的 AI 玩家。
- **🤖 Multi-Agent 协作架构**：基于 `LangChain4j` 和 `LangGraph`，设计了 DM、Player、Judge 和 Summary 四大专属 Agent，各司其职，推动游戏逻辑与多轮推理的运转。
- **🧠 混合多级记忆引擎**：首创“短期/中期/长期”三级记忆系统。结合 Caffeine 缓存与 `Milvus` 向量数据库实现长记忆 RAG，解决 LLM 在长文本中的“金鱼记忆”问题。
- **⚡ 高性能与流式处理**：后端采用 Spring Boot 3 结合 Reactive Streams 实现剧本的边创作边预览；通过 WebSocket 实现低延迟实时双向通信。

### 📱 新月集家教版 —— AI 智能家教中介平台 *(私有仓库)*
连接家教老师与家长的智能撮合平台，集成 AI 内容优化与智能客服，实现高效精准的匹配。
- **🤖 LangChain4j AI 增强**：基于大模型的帖子内容优化、智能客服 Agent，提升用户体验与平台转化效率。
- **💬 实时双向通信**：WebSocket 聊天系统，支持家教与家长即时对话。
- **🛠️ 全栈工程实践**：Spring Boot 后端 + PostgreSQL + pgvector 向量存储，Vue 3 Web 管理后台。

### 🤖 ToThink —— PC 端多智能体任务自动化平台 *(私有仓库)*
基于视觉感知的层次化多智能体协作框架，实现 PC 端复杂任务的自主规划与执行。支持 Chrome、Word、WeChat 等生产力场景的自动化控制。
- **🎯 层次化 Agent 架构**：采用多智能体协作模式，通过任务分解、规划决策、动作执行的分层结构，提升复杂任务链的成功率。
- **👁️ 主动视觉感知**：针对 PC 平台密集交互元素设计的感知模块，结合 OCR 和视觉定位实现精准的界面元素识别与操作。
- **🖥️ Electron 桌面应用**：集成用户认证、任务历史管理、多设备同步等功能，提供开箱即用的桌面端体验。

### 🛒 [Order-System —— 高并发异步商城订单系统](https://github.com/Zewang0217/order-system)
基于经典的微服务解耦思想打造的高性能业务后端。
- 基于 `RabbitMQ` 实现了订单创建、库存扣减的**异步化解耦**。
- 有效提升了系统的瞬时吞吐量，实现电商大促场景下的**流量削峰填谷**，保障高并发场景下数据的一致性与高可用。

---

## 🛠️ 更多极客探索 (Other Explorations)

- 🐧 **[shell-ECNUChat](https://github.com/Zewang0217/shell-ECNUChat)**: 基于 Python 的 CLI 工具，调用 ECNUChat 模型实现**自然语言转 Linux 命令**，并内置教学/助教模式。
- 📊 **[slidev-skill](https://github.com/Zewang0217/slidev-skill)**: 驱动 Agent 通过自然语言自动生成、排版优雅 Slidev 幻灯片的拓展技能栈 (Vue)。
- 📝 **[myBlog_v2.0](https://github.com/Zewang0217/myBlog_v2.0)**: 基于最新 **Java 21** 特性与前后端分离架构（Vue）开发的现代化个人博客平台。

---

## 📈 开源统计 (GitHub Stats)

<div align="center">
    <img src="https://metrics.run/Zewang0217?base=header%2C+activity%2C+community%2C+repositories%2C+metadata&config.timezone=Asia%2FShanghai" alt="Metrics" width="100%" />
  <br/><br/>

  <img src="https://github-readme-stats-sigma-five.vercel.app/api?username=Zewang0217&show_icons=true&theme=tokyonight&hide_border=true" height="170px" />
  <img src="https://github-readme-stats-sigma-five.vercel.app/api/top-langs/?username=Zewang0217&layout=compact&theme=tokyonight&hide_border=true" height="170px" />

  <br/><br/>

  <img src="https://github-readme-streak-stats.herokuapp.com/?user=Zewang0217&theme=tokyonight&hide_border=true" height="170px" />
  
  <br/>
  
  <p align="right">
    <img src="https://komarev.com/ghpvc/?username=Zewang0217&label=Profile%20views&color=2563eb&style=flat" alt="Visitor Count" />
  </p>
</div>
