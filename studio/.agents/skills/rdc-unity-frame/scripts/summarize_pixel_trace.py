"""Print selected RenderDoc pixel-trace registers without dumping the full JSON."""
import json
import sys


def main():
    with open(sys.argv[1], encoding="utf-8") as stream:
        trace = json.load(stream)
    lo, hi = int(sys.argv[2]), int(sys.argv[3])
    for pixel in trace["pixels"]:
        print("PIXEL", pixel["x"], pixel["y"])
        for step in pixel["steps"]:
            instruction = step["nextInstruction"]
            if not lo <= instruction <= hi:
                continue
            changed = []
            for change in step.get("changes", []):
                after = change["after"]
                if after["name"].startswith(("r", "o")):
                    values = ",".join("%.3f" % value for value in after["f32v"])
                    changed.append("%s=[%s]" % (after["name"], values))
            if changed:
                print(instruction, " ".join(changed))


if __name__ == "__main__":
    main()
