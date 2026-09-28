"""Audit PS31475's skin light-color mixer using saved RenderDoc pixel traces.

The expression below is the literal data flow of instructions 318-329, not a
fit to the final render target. Earlier instructions compute the band weights.
"""
import json
import sys


def state_after(pixel, instruction, register):
    for step in pixel["steps"]:
        if step["nextInstruction"] != instruction:
            continue
        for change in step.get("changes", []):
            after = change["after"]
            if after["name"] == register:
                return after["f32v"]
    raise ValueError("missing %s at instruction %s" % (register, instruction))


def analyze(pixel):
    base = state_after(pixel, 178, "r11")[:3]
    shadow_color = state_after(pixel, 302, "r16")[:3]
    middle_color = state_after(pixel, 300, "r15")[:3]
    lit_color = state_after(pixel, 279, "r18")[:3]
    dark_weight = state_after(pixel, 207, "r13")[1]
    middle_weight = state_after(pixel, 209, "r16")[0]
    lit_weight = state_after(pixel, 261, "r8")[3]
    light_dot = state_after(pixel, 183, "r10")[3]
    band_coordinate = state_after(pixel, 192, "r3")[2]
    mixed = state_after(pixel, 330, "r11")[:3]

    # PS 31475: 319-321 normalize the prior light response; 322-329
    # combine diffuse-color rows selected from cb3[39..48]. The r18 and
    # r12 states include the exact four-band weights computed in 183-265.
    light = state_after(pixel, 319, "r11")[:3]
    direct = state_after(pixel, 324, "r18")[:3]
    bands = state_after(pixel, 328, "r12")[:3]
    # Instruction 321 stores the exact normalized light term. It avoids
    # rounding through the printed reciprocal when checking the trace.
    normalized = state_after(pixel, 321, "r17")[:3]
    reconstructed = [light[i] * direct[i] + normalized[i] * bands[i]
                     for i in range(3)]
    return {
        "pixel": [pixel["x"], pixel["y"]],
        "normal_dot_light": light_dot,
        "band_coordinate": band_coordinate,
        "weights": {"dark": dark_weight, "middle": middle_weight,
                    "lit": lit_weight},
        "selected_colors": {"dark": shadow_color,
                            "middle": middle_color, "lit": lit_color},
        "pre_band_light": base,
        "reconstructed_instruction_330": reconstructed,
        "source_instruction_330": mixed,
        "max_absolute_error": max(abs(a - b) for a, b in zip(reconstructed, mixed)),
    }


def main():
    with open(sys.argv[1], encoding="utf-8") as stream:
        trace = json.load(stream)
    result = json.dumps([analyze(pixel) for pixel in trace["pixels"]],
                        ensure_ascii=False, indent=2)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as stream:
            stream.write(result + "\n")
    else:
        print(result)


if __name__ == "__main__":
    main()
