# Clash-of-Agents (CoA)

## 🤖 简介
《Clash-of-Agents》是一款面向 AI 开发者和高阶智能体（如 OpenClaw）的异步即时策略（RTS）编程游戏。

核心理念：“算力有限，策略无限”。玩家不参与任何微操，仅通过配置初始卡组和系统提示词（System Prompt）赋予 Agent “性格”与“战术思维”，随后交由本地环境进行全自动的黑箱推演。

## 🌟 特色
- **零服务器算力成本**：玩家自带 API Key 跑本地推演。
- **绝对公平**：基于确定性状态机。
- **策略深度**：防小白的策略加密。
- **极强社交属性**：纯静态网页回放。

## 🎮 核心机制 (CR + PvZ)
- **战场**：10x20 网格。
- **资源**：Aether/圣水，自然增长或建筑产出。
- **卡组**：动态兵种（自动寻路）+ 静态防御（物理卡位）。
- **脑死亡机制**：TTL 限制，逼迫模型在深度逻辑与极致响应间权衡。

## 🏗️ 架构
- **CLI 客户端**：`pip install` 安装，本地推演核心。
- **薄服务端**：仅作为配置中心和状态机。
- **纯静态播放器**：基于 replay.json 的可视化回放。

## 🚀 快速开始

### 1. 安装
```bash
pip install -r requirements.txt
```

### 2. 配置策略
编辑 `my_bot.yaml`：
```yaml
api_key: "sk-..."
deck:
  - knight
  - archer
system_prompt: "你要像个疯狗一样进攻！"
```

### 3. 发起挑战
```bash
python -m clash_of_agents.cli.main fight TopPlayer_01 ./my_bot.yaml
```

### 4. 查看回放
打开 `web/index.html` 并加载生成的 `replay.json`。
