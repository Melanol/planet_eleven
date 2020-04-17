MAX_LINE_LENGTH = 82

file = open('planet_eleven.py', 'r')
file_contents = file.read()

lines = file_contents.split('\n')

long_lines_ns = []
for i, line in enumerate(lines):
    if len(line) > MAX_LINE_LENGTH:
        long_lines_ns.append(i + 1)

print(long_lines_ns)