import os, subprocess, json, shutil
from flask import Flask, render_template_string, request, redirect, session, url_for, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "rebate2026")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "refresh-token")

# Path to dashboard HTML
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_HTML = os.path.join(BASE_DIR, "rebate_dashboard.html")
REFRESH_SCRIPT = os.path.join(BASE_DIR, "..", "scripts", "rebate_dashboard.py")

# HTML templates
LOGIN_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>蓝标欧加海外返点看板 - 登录</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { 
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    height: 100vh; display: flex; align-items: center; justify-content: center;
}
.card { background: white; border-radius: 12px; padding: 40px; width: 380px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
.card h1 { font-size: 20px; font-weight: 600; margin-bottom: 4px; color: #333; }
.card p { font-size: 13px; color: #888; margin-bottom: 24px; }
.input-group { margin-bottom: 16px; }
.input-group label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; font-weight: 500; }
.input-group input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; outline: none; }
.input-group input:focus { border-color: #1565c0; box-shadow: 0 0 0 3px rgba(21,101,192,0.1); }
.btn { width: 100%; padding: 10px; background: #1565c0; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; }
.btn:hover { background: #0d47a1; }
.error { color: #d32f2f; font-size: 13px; margin-top: 8px; text-align: center; }
</style>
</head>
<body>
<div class="card">
    <h1>蓝标欧加海外返点看板</h1>
    <p>请输入密码以查看数据看板</p>
    <form method="post">
        <div class="input-group">
            <label>访问密码</label>
            <input type="password" name="password" placeholder="请输入密码" autofocus>
        </div>
        <button type="submit" class="btn">进入看板</button>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </form>
</div>
</body>
</html>"""

@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        if request.form.get("password") == DASHBOARD_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "密码错误，请重试"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if os.path.exists(DASHBOARD_HTML):
        return send_from_directory(BASE_DIR, "rebate_dashboard.html")
    return "<h1>看板数据尚未生成</h1><p>管理员需要先运行数据刷新脚本。请稍后再试。</p>", 503

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/refresh")
def refresh():
    token = request.args.get("token")
    if not token or token != REFRESH_TOKEN:
        return {"error": "unauthorized"}, 401
    
    if not os.path.exists(REFRESH_SCRIPT):
        return {"error": "refresh script not found"}, 500
    
    try:
        result = subprocess.run(
            ["uv", "run", "python3", REFRESH_SCRIPT],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(REFRESH_SCRIPT)
        )
        # Copy the generated HTML to the server directory
        src = os.path.join(os.path.dirname(REFRESH_SCRIPT), "..", "rebate_dashboard.html")
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, DASHBOARD_HTML)
        
        return {
            "status": "ok",
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()[:500]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/api/upload", methods=["POST"])
def upload_html():
    """Receive HTML file from local cron job"""
    token = request.args.get("token")
    if not token or token != REFRESH_TOKEN:
        return {"error": "unauthorized"}, 401
    
    if "file" not in request.files:
        return {"error": "no file"}, 400
    
    f = request.files["file"]
    f.save(DASHBOARD_HTML)
    return {"status": "ok", "size": os.path.getsize(DASHBOARD_HTML)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)