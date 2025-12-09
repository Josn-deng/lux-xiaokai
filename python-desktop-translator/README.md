# Python Desktop Translator

## 项目简介
Python Desktop Translator 是一个桌面翻译软件，具有悬浮窗功能，用户可以通过悬浮窗访问多种翻译和文本处理服务，包括 AI 翻译、文本润色、AI 问答、语音翻译等。该软件还提供了设置功能，允许用户配置 AI 服务器、模型、密钥和开机自启等参数。

## 功能特性
- **悬浮窗**：在桌面上显示的可移动窗口，方便用户快速访问翻译功能。
- **AI 翻译**：通过 AI 技术实现高效的文本翻译。
- **文本润色**：提供文本优化和润色服务。
- **AI 问答**：用户可以通过该功能提问并获取 AI 的回答。
- **语音翻译**：支持语音输入并进行翻译。
- **设置功能**：用户可以配置应用程序的各项参数，包括 AI 服务器、模型、密钥和开机自启选项。

## 项目结构
```
python-desktop-translator
├── src
│   ├── main.py
│   ├── core
│   ├── ui
│   ├── services
│   ├── models
│   ├── config
│   ├── utils
│   ├── resources
│   └── startup
├── tests
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## 安装与运行
1. 克隆项目到本地：
   ```
   git clone <repository-url>
   ```
2. 进入项目目录：
   ```
   cd python-desktop-translator
   ```
3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
4. 运行应用程序：
   ```
   python src/main.py
   ```

## 贡献
欢迎任何形式的贡献！请提交问题或拉取请求。

## 许可证
该项目遵循 MIT 许可证。