import asyncio
import json
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


CAPTURE = r"E:\KianaFrame38112Workspace\Frame38112Capture\capture_frame38112.rdc"
OUTPUT = Path(r"E:\KianaFrame38112Workspace\Frame38112Capture\analysis-frame38112\transparent-cloth")


def payload(result):
    for item in result.content:
        text = getattr(item, "text", "")
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return {}


async def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    async with streamablehttp_client("http://127.0.0.1:8765/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            opened = payload(await session.call_tool("open_capture", {"capture_path": CAPTURE}))
            results = {"open_capture": opened}
            for name, start, end in (("eid1610", 1550, 1620), ("eid1868", 1820, 1880), ("late_chain", 1330, 2490)):
                directory = OUTPUT / name
                directory.mkdir(parents=True, exist_ok=True)
                result = await session.call_tool(
                    "identify_drawcalls",
                    {
                        "event_id_min": start,
                        "event_id_max": end,
                        "output_dir": str(directory),
                        "render_target": 53234,
                    },
                )
                results[name] = payload(result)
                (directory / "result.json").write_text(
                    json.dumps(results[name], ensure_ascii=False, indent=2), encoding="utf-8"
                )
            (OUTPUT / "stage-results.json").write_text(
                json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(json.dumps({key: len(value.get("draws", value.get("actions", []))) if isinstance(value, dict) else 0 for key, value in results.items()}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
