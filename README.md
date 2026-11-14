# AI Key 批量测试控制台

一个零依赖、单文件的 AI API Key 批量可用性测试工具。粘贴一批 Key，一键探测它们在各个模型厂商下的真实可用状态：能否列模型、能否完成对话、失败原因是什么。

纯 Python 标准库实现，无需 `pip install`，一个 `app.py` 跑起来就是一个带 Web 界面的控制台。

## 功能

- **多厂商分 Tab**：OpenAI / Claude (Anthropic) / DeepSeek / Gemini / xAI / 通用 (任意 OpenAI 兼容中转站)
- **批量探测**：粘贴多行 Key，并发测试，逐条给出结论
- **真实可用性验证**：先 `GET /models` 验证鉴权，再发一次最小对话请求验证配额与模型可用性，不是只看 HTTP 200
- **按结论筛选**：可用 / 无效 Key / 无额度 / 限流 / 模型不存在 / 网络错误等分类查看
- **拉取模型列表**：用有效 Key 实时拉取该账号可用的模型
- **导出结果**：把测试结果导出留存
- **主题切换**：系统 / 深色 / 浅色
- **Key 脱敏展示**：界面上只显示前后几位，避免误泄漏

## 支持的厂商

| 厂商 | 鉴权方式 | 列模型 | 对话 |
|---|---|---|---|
| OpenAI | `Authorization: Bearer` | `GET /models` | `POST /chat/completions` |
| Claude | `x-api-key` + `anthropic-version` | `GET /models` | `POST /messages` |
| DeepSeek | `Authorization: Bearer` | `GET /models` | `POST /chat/completions` |
| Gemini | `x-goog-api-key` | `GET /models` | `POST /models/{model}:generateContent` |
| xAI | `Authorization: Bearer` | `GET /models` | `POST /chat/completions` |
| 通用 | `Authorization: Bearer` | `GET /models` | `POST /chat/completions` |

「通用」用于测试任意 OpenAI 兼容的中转站或自建网关，基地址自己填。

## 运行

需要 Python 3.8+，无第三方依赖。

```bash
python3 app.py --host 127.0.0.1 --port 8787
```

然后浏览器打开 `http://127.0.0.1:8787`。

默认监听 `0.0.0.0:8787`，**建议显式指定 `--host 127.0.0.1`**，只在本机访问；如需对外提供服务，请在前置反向代理上加认证与 TLS。

## 使用方式

1. 选择厂商 Tab（或「通用」填自己的中转站地址）
2. 粘贴一批 Key，每行一个
3. 选择要测试的模型
4. 点开始测试，等待并发探测完成
5. 按结论筛选，把无效 / 无额度的 Key 挑出来

## 安全说明

- Key 只在本机内存中处理，不发往任何第三方服务，只发往你选择的厂商官方 API（或你自定义的地址）
- 界面上 Key 始终脱敏显示
- 本工具不做任何 Key 生成、买卖或共享，仅做可用性检测

## 免责声明

仅供测试你自己合法持有的 API Key 使用。请遵守各服务商的条款。

## License

MIT
