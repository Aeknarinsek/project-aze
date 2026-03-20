with open('ai_agents/generator_agent.py', encoding='utf-8') as f:
    lines = f.readlines()
cutoff = None
for i, line in enumerate(lines):
    if line.strip() == 'main()' and i > 0 and '__name__' in lines[i-1]:
        cutoff = i + 1
        break
if cutoff:
    with open('ai_agents/generator_agent.py', 'w', encoding='utf-8') as f:
        f.writelines(lines[:cutoff])
    print(f'Truncated to {cutoff} lines — done')
else:
    print('Cutoff not found')
