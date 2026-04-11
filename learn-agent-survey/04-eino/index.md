---
layout: default
title: "Eino：字节跳动的 Go 语言 Agent 框架"
description: 字节跳动开源的 Go 语言 AI 应用框架——组件化设计、类型安全的 Pipeline、流式处理原生支持
eyebrow: 框架调研 · 04
---

# Eino：字节跳动的 Go 语言 Agent 框架

Eino 是字节跳动 2024 年开源的 Go 语言 AI 应用框架，用于构建基于 LLM 的应用和 Agent。名字来源于希腊语“εἶναι”（存在），定位是**生产级 Go AI 框架**。

GitHub：[cloudwego/eino](https://github.com/cloudwego/eino)

## 为什么是 Go

Python 是 AI 生态的主流语言，Go 有什么理由？

- **高并发**：Go 的 goroutine 处理大量并发 Agent 请求天然高效
- **低延迟**：没有 GIL，没有 Python 的解释器开销
- **部署简单**：单二进制，无依赖，容器化友好
- **类型安全**：强类型 + 接口约束，减少运行时错误
- **字节跳动自用**：内部系统大量 Go，Eino 直接复用

## 安装

```bash
go get github.com/cloudwego/eino@latest
```

## 核心概念

| 概念 | 说明 |
|------|------|
| `Component` | 最小功能单元，如 ChatModel、Retriever、Tool |
| `Graph` / `Chain` | 把组件连接起来的流程容器 |
| `Stream` | 原生流式处理，每个组件都支持流式 I/O |
| `Lambda` | 把任意函数包装成组件 |

## 最小示例

```go
package main

import (
    "context"
    "fmt"

    "github.com/cloudwego/eino/components/model"
    "github.com/cloudwego/eino-ext/components/model/openai"
)

func main() {
    ctx := context.Background()

    // 初始化 ChatModel（这里用 OpenAI）
    chatModel, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
        Model:  "gpt-4o-mini",
        APIKey: "your-openai-key",
    })
    if err != nil {
        panic(err)
    }

    // 发送消息
    msgs := []*model.Message{
        {Role: model.RoleUser, Content: "用中文介绍一下 Eino 框架"},
    }

    resp, err := chatModel.Generate(ctx, msgs)
    if err != nil {
        panic(err)
    }
    fmt.Println(resp.Content)
}
```

## Chain：顺序流水线

```go
package main

import (
    "context"

    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"
)

func main() {
    ctx := context.Background()

    // 构建 Chain
    chain := compose.NewChain[string, string]()

    chain.
        AppendLambda(compose.InferLambdaType(func(ctx context.Context, input string) (string, error) {
            // 第一步：预处理
            return "预处理: " + input, nil
        })).
        AppendChatModel(chatModel).         // 第二步：LLM 处理
        AppendLambda(compose.InferLambdaType(func(ctx context.Context, msg *schema.Message) (string, error) {
            // 第三步：提取文本
            return msg.Content, nil
        }))

    // 编译
    runnable, err := chain.Compile(ctx)
    if err != nil {
        panic(err)
    }

    // 运行
    result, err := runnable.Invoke(ctx, "什么是 Agent？")
    if err != nil {
        panic(err)
    }
    fmt.Println(result)
}
```

## Graph：有向图工作流

```go
package main

import (
    "context"

    "github.com/cloudwego/eino/compose"
    "github.com/cloudwego/eino/schema"
)

// 定义状态
type ResearchState struct {
    Topic   string
    Facts   []string
    Summary string
}

func main() {
    ctx := context.Background()

    graph := compose.NewGraph[ResearchState, ResearchState]()

    // 添加节点
    graph.AddLambdaNode("fetch", compose.InferLambdaType(
        func(ctx context.Context, state ResearchState) (ResearchState, error) {
            state.Facts = append(state.Facts, "事实1: "+state.Topic+"相关内容")
            return state, nil
        },
    ))

    graph.AddLambdaNode("summarize", compose.InferLambdaType(
        func(ctx context.Context, state ResearchState) (ResearchState, error) {
            state.Summary = "关于" + state.Topic + "的摘要：" + state.Facts[0]
            return state, nil
        },
    ))

    // 连接节点
    graph.AddEdge(compose.START, "fetch")
    graph.AddEdge("fetch", "summarize")
    graph.AddEdge("summarize", compose.END)

    // 编译运行
    runnable, _ := graph.Compile(ctx)
    result, _ := runnable.Invoke(ctx, ResearchState{Topic: "LangGraph"})
    fmt.Println(result.Summary)
}
```

## 流式处理

Eino 的流式是原生设计，不是后加的：

```go
// 流式生成
stream, err := chatModel.Stream(ctx, msgs)
if err != nil {
    panic(err)
}
defer stream.Close()

for {
    chunk, err := stream.Recv()
    if err != nil {
        break
    }
    fmt.Print(chunk.Content)
}
fmt.Println()
```

## Tool（工具调用）

```go
import "github.com/cloudwego/eino/components/tool"

// 定义工具
type WeatherInput struct {
    City string `json:"city" jsonschema:"description=城市名称"`
}

type WeatherOutput struct {
    Weather string `json:"weather"`
}

weatherTool := tool.NewTool(
    tool.WithName("get_weather"),
    tool.WithDesc("获取城市天气"),
    tool.WithFunc(func(ctx context.Context, input *WeatherInput) (*WeatherOutput, error) {
        data := map[string]string{
            "北京": "晴天 25°C",
            "上海": "多云 22°C",
        }
        weather, ok := data[input.City]
        if !ok {
            weather = "暂无数据"
        }
        return &WeatherOutput{Weather: weather}, nil
    }),
)

// 绑定到 ChatModel
chatModel.BindTools([]tool.BaseTool{weatherTool})
```

## 与字节跳动生态集成

Eino 在字节内部有深度集成：

```go
// 豆包（ByteDance LLM）
import "github.com/cloudwego/eino-ext/components/model/ark"

doubaoModel, _ := ark.NewChatModel(ctx, &ark.ChatModelConfig{
    APIKey:  "your-ark-key",
    Model:   "ep-xxxxx",  // 豆包 endpoint
})
```

## 优缺点

**优点：**
- Go 原生，并发性能优秀
- 流式处理原生支持，不是事后叠加
- 强类型约束，减少运行时错误
- 字节跳动生产验证，豆包集成好
- 单二进制部署，运维简单

**缺点：**
- Python AI 生态的工具无法直接用
- 社区比 Python 框架小得多
- 文档主要面向 Go 开发者，AI 背景的人可能不熟悉 Go

## 适合什么场景

- Go 技术栈的后端团队
- 高并发 Agent 服务（每秒大量请求）
- 需要低延迟、低资源消耗的部署
- 字节跳动 / 豆包生态下的应用
