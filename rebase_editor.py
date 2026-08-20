import sys
with open(sys.argv[1], 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('pick ') and 'feat(ml):' in line:
        new_lines.append(line.replace('pick ', 'reword '))
    else:
        new_lines.append(line.replace('safhera model', 'sakhi model'))

with open(sys.argv[1], 'w') as f:
    f.writelines(new_lines)
