"""Generate MCP client settings for this installation's actual location."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
command = str(root / "python_mcp/python.exe")
args = [str(root / "mcp/launch.py")]
environment = {"PYTHONUTF8":"1","KIANA_HOME":str(root)}
config = {"mcpServers":{"kiana":{"command":command,"args":args,"env":environment}}}
(root / "mcp-client.json").write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding="utf-8")
toml = '[mcp_servers.kiana]\ncommand = ' + json.dumps(command) + '\nargs = ' + json.dumps(args)
toml += '\nstartup_timeout_sec = 30\ntool_timeout_sec = 300\n[mcp_servers.kiana.env]\n'
toml += '\n'.join(k + ' = ' + json.dumps(v) for k,v in environment.items()) + '\n'
(root / "mcp-codex.toml").write_text(toml,encoding="utf-8")
print("MCP settings generated in " + str(root))
