"""一次性脚本：注册 FastapiAdmin Agent 并生成 MCP 配置"""
import urllib.request
import json
import sys

BASE = "http://localhost:8001"

def post(path, data=None):
    body = json.dumps(data).encode() if data else b''
    req = urllib.request.Request(BASE + path, data=body, method='POST',
                                 headers={"Content-Type": "application/json"})
    if hasattr(post, 'cookie'):
        req.add_header("Cookie", post.cookie)
    r = urllib.request.urlopen(req)
    resp = json.loads(r.read().decode())
    cookie = r.headers.get("Set-Cookie")
    if cookie:
        post.cookie = cookie.split(";")[0]
    return resp

# 1. 登录
print("=== 1.1 登录 ===")
r = post("/api/login", {"username": "admin", "password": "admin"})
print(r)
if not r.get("success"):
    sys.exit(1)

# 2. 生成 Admin Token
print("\n=== 1.2 生成 Admin Token ===")
r = post("/api/admin/token/generate")
print(r)
admin_token = r.get("admin_token", "")

# 3. 注册 Agent
AGENT_ID = "FastapiAdmin"
print(f"\n=== 1.3 注册 Agent: {AGENT_ID} ===")
r = post("/api/admin/agent/register", {
    "agent_id": AGENT_ID,
    "agent_name": "FastapiAdmin",
    "admin_token": admin_token,
    "agent_type": "BUSINESS",
    "description": "FastapiAdmin Claude Code Agent"
})
print(json.dumps(r, indent=2, ensure_ascii=False))

# 4. 注册 MCP 认证凭证
MCP_TOKEN = "agt_fastapi_admin_2026"
print(f"\n=== 1.4 注册 MCP 凭证 (token={MCP_TOKEN}) ===")
sys.path.insert(0, r"F:\mygit2\AI-Agent-Infra-with-OracleDB-Community-Edition\scripts")
from lib import agent_registration
agent_registration.set_status(AGENT_ID, "DISABLED", actor="admin-setup")
agent_registration.register_agent(
    agent_id=AGENT_ID, owner_ref="administrator",
    runtime="claude-code", environment="production",
    node_id="local-dev", capabilities=["mcp", "memory", "knowledge"],
    credential=MCP_TOKEN, credential_version="1", created_by="admin-setup",
)
auth = agent_registration.authenticate_agent(AGENT_ID, MCP_TOKEN)
print("MCP Auth:", "PASS" if auth else "FAIL")

# 5. 生成 .mcp.json
print(f"\n=== 步骤 2：.mcp.json 内容（复制到你的项目根目录） ===")
mcp_config = {
    "mcpServers": {
        "chuanxu": {
            "command": r"F:\mygit2\AI-Agent-Infra-with-OracleDB-Community-Edition\.venv\Scripts\python.exe",
            "args": [
                r"F:\mygit2\AI-Agent-Infra-with-OracleDB-Community-Edition\scripts\mcp_server_main.py",
                "--transport", "stdio"
            ],
            "env": {
                "AI_AGENT_ID": AGENT_ID,
                "AI_AGENT_TOKEN": MCP_TOKEN
            }
        }
    }
}
print(json.dumps(mcp_config, indent=2))
