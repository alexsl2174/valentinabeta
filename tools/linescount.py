import os

total = 0
for fn in os.listdir('../cogs'):
  if fn.endswith('.py'):
    with open(f'../cogs/{fn}', encoding='utf8') as f:
      total += len(f.readlines())

for fn in os.listdir('.'):
  if fn.endswith('.py'):
    with open(f'./{fn}', encoding='utf8') as f:
      total += len(f.readlines())

print(f'{total:,} lines')