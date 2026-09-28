"""Exercise real MCP initialization, schema listing and live GUI RPC over stdio."""
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    package = Path(sys.argv[1]).resolve()
    params = StdioServerParameters(command=str(package/"python_mcp/python.exe"),
        args=[str(package/"mcp/launch.py")],
        env=dict(os.environ,PYTHONUTF8="1",KIANA_HOME=str(package),KIANA_PID=sys.argv[2]))
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            assert len(names) == len(set(names))
            assert all(n in names for n in ("ping","export_fbx","set_features","get_pipeline_state",
                                            "capture_nsight_d3d12","convert_nsight_to_rdc"))
            ping = await session.call_tool("ping",{})
            assert not ping.isError
            value = json.loads(ping.content[0].text)
            assert value["status"] == "ok"
            status = await session.call_tool("get_capture_status",{})
            result = {"tool_count":len(names),"tools":names,"ping":value,
                      "capture_status":json.loads(status.content[0].text)}
            print(json.dumps(result,indent=2))
            Path("build-early-exports/kiana-mcp-protocol.json").write_text(json.dumps(result,indent=2),encoding="utf-8")

asyncio.run(main())
