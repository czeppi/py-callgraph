from pathlib import Path
from filesystem import RegularFile

from proglib import Program


main_file = RegularFile(Path('selftest.py'))
prg: Program = Program(main_file)
prg.build()

for module in prg.iter_modules():
    print(module.fullname)
    for call in module._call_graph.calls:
        print('  {}'.format(call))