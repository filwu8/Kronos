import importlib
import sys
sys.path.insert(0, '.')
mod = importlib.import_module('app.api')
print('OK', getattr(mod, 'app', None).title if hasattr(mod, 'app') else 'no app')

