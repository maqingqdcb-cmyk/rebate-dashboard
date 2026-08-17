# 蓝标欧加海外返点看板 - 部署说明

## 本地测试

```bash
cd rebate_server
cp .env.example .env
PORT=8080 uv run python3 app.py
```

打开浏览器访问 http://localhost:8080，密码：rebate2026

## 部署到 Render

1. 在 [render.com](https://render.com) 注册账号
2. 点 "New +" → "Web Service"
3. 连接你的 GitHub 仓库，或选择 "Upload File"
4. 配置：
   - **Name**: `rebate-dashboard`
   - **Root Directory**: `rebate_server`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
5. 添加环境变量：
   - `DASHBOARD_PASSWORD`：设置一个密码，分享给同事
   - `FLASK_SECRET_KEY`：随机字符串（点击 Generate）
   - `REFRESH_TOKEN`：随机字符串（点击 Generate）
6. 部署完成后，你会得到一个 URL 如 `https://rebate-dashboard.onrender.com`

## 配置每日自动刷新

部署后，在本地设置两个环境变量，cron 会自动上传更新：

```bash
export RENDER_URL="https://rebate-dashboard.onrender.com"
export REFRESH_TOKEN="你在Render上设置的值"
```

然后每天早上 9:00 的 cron 会自动刷新数据并上传到 Render。

## 分享给同事

把以下信息发给同事：
- 看板链接：`https://rebate-dashboard.onrender.com`
- 访问密码：`你设置的 DASHBOARD_PASSWORD`