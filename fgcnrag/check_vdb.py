with open(r'C:\Users\Windows\Desktop\lindaiyu\fgcnrag\fgcn\database\vdb_init.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f'Total lines: {len(lines)}')
    print('First 30 lines:')
    for i, l in enumerate(lines[:30]):
        print(f'{i+1}: {repr(l)[:80]}')
