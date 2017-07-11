'''
python library by @Sine

for updating code changes at development time,
import or reload will delete all modules in sys.modules that are from this package
'''

def deleteAllModules():
    import sys
    for i in sys.modules.copy():
        if i.startswith('sine.'):
            del sys.modules[i]

deleteAllModules()

import decorator
import helpers
