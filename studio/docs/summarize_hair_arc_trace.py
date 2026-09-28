import json
import sys

trace = json.load(open('docs/frame38112-hair-arc-trace.json', encoding='utf-8'))
numbers = set(range(55, 65)) | set(range(335, 396)) | set(range(580, 616)) | set(range(645, 681))
names = {'r0', 'r1', 'r2', 'r3', 'r12', 'r13', 'r14', 'r15', 'o0'}
if len(sys.argv) > 1:
    names = set(sys.argv[1].split(','))
    numbers = set(range(0, 1000))
if len(sys.argv) > 3:
    numbers = set(range(int(sys.argv[2]), int(sys.argv[3]) + 1))
for pixel in trace['pixels']:
    print('PIX', pixel['x'], pixel['y'])
    for step in pixel['steps']:
        instruction = step['nextInstruction']
        if instruction not in numbers:
            continue
        values = [change['after'] for change in step.get('changes', []) if change['after']['name'] in names]
        if values:
            print(instruction, [(value['name'], [round(component, 3) for component in value['f32v']]) for value in values])
