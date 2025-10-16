from RestrictedPython import compile_restricted, safe_builtins, limited_builtins, utility_builtins
from RestrictedPython.Guards import guarded_iter_unpack_sequence, guarded_unpack_sequence
from RestrictedPython.Eval import default_guarded_getiter
from unittest.mock import patch
from func_timeout import func_timeout
import traceback
import operator  # Adicione esta importação para usar operadores padrão do Python

DANGEROUS_LIST = [
    # 'builtins.open',
    # 'builtins.input',
    # 'os.system', 
    # 'os.popen',
    # 'subprocess.call',
    # 'subprocess.Popen',
    # 'pty.spawn',
    # 'platform.os.system',
    # 'imp.load_source',
    # 'imp.os',
    'pip.main'
]

class SafePythonCompilerException(Exception):

    pass

class SafePythonCompiler:

    class _Patcher:

        def __init__(self, parent):

            self.parent = parent
            self._patchers = []
            for forbidden in self.parent._forbidden_modules:
                self._patchers.append(patch(forbidden, side_effect=Exception('Forbidden code usage. You are trying to run a forbidden code.')))

        def __enter__(self):
            for p in self._patchers:
                p.start()

        def __exit__(self, type, value, traceback):
            for p in self._patchers:
                p.stop()

    def __init__(self, safe_import_modules=[], forbidden_modules=[], max_for=100, exec_timeout=5):

        self._safe_import_modules = safe_import_modules
        self._forbidden_modules = forbidden_modules
        self._max_for = max_for
        self._exec_timeout = exec_timeout
        self.loc = {}
    
    def _make_safe_builtins(self):

        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            package_name = name.split('.')[0]
            if package_name not in self._safe_import_modules:
                raise Exception("{} is not an allowed package.".format(package_name))
            imported = __import__(name, globals, locals, fromlist, level)
            return imported

        def safe_for(*args, **kwargs):

            try:
                if len(args[0]) > self._max_for:
                    raise SafePythonCompilerException("Too much items in a for loop.")
            except TypeError:
                # Handle cases where args[0] does not support len (e.g., enumerate)
                pass

            return default_guarded_getiter(*args, **kwargs)

        def safe_unpack_iter(*args, **kwargs):

            return guarded_iter_unpack_sequence(*args, **kwargs)
        
        def safe_getitem(value, key):
            try:
                return value[key]
            except IndexError:
                if isinstance(key, slice):
                    return []
                else:
                    raise
            except TypeError:
                return None

        def safe_write(value):

            return value

        my_safe_builtins = safe_builtins.copy()
        my_safe_builtins.update(limited_builtins) # Including range, list and tuple
        my_safe_builtins.update(utility_builtins) # Including len, sum, min, max, etc
        my_safe_builtins.update(
            {
                '__import__': safe_import,
                '_getitem_': safe_getitem,
                '_write_': safe_write,
                'min': min,  # Ensure min is explicitly included
                'max': max,  # Ensure max is explicitly included
                'sum': sum,  # Ensure sum is explicitly included
                'dict': dict,  # Ensure dict is explicitly included
                'next': next,  # Ensure next is explicitly included
                'enumerate': enumerate,  # Ensure enumerate is explicitly included
                'sorted': sorted,  # Ensure sorted is explicitly included
                'list': list,  # Ensure list is explicitly included
                'tuple': tuple,  # Ensure tuple is explicitly included
                '_inplacevar_': lambda x, op, y: {
                    operator.iadd: lambda a, b: a + b,  # x += y
                    operator.isub: lambda a, b: a - b,  # x -= y
                    operator.imul: lambda a, b: a * b,  # x *= y
                    operator.itruediv: lambda a, b: a / b,  # x /= y
                    operator.ifloordiv: lambda a, b: a // b,  # x //= y
                    operator.imod: lambda a, b: a % b,  # x %= y
                    operator.ipow: lambda a, b: a ** b,  # x **= y
                    operator.iand: lambda a, b: a & b,  # x &= y
                    operator.ior: lambda a, b: a | b,  # x |= y
                    operator.ixor: lambda a, b: a ^ b,  # x ^= y
                    operator.ilshift: lambda a, b: a << b,  # x <<= y
                    operator.irshift: lambda a, b: a >> b,  # x >>= y
                }.get(op, lambda a, b: SafePythonCompilerException(f"Unsupported operator {op}"))(x, y),
            }
        )
        
        self.restricted_globals = dict(
            __builtins__=my_safe_builtins,
            _iter_unpack_sequence_=safe_unpack_iter,
            _getiter_=safe_for,
            _unpack_sequence_=guarded_unpack_sequence,
        )

    def _check_source_commands(self, source_code):

        pass

    def compile(self, source_code):

        self._make_safe_builtins()

        self._check_source_commands(source_code)

        try:
           
            byte_code = compile_restricted(
                source_code,
                filename='<inline>',
                mode='exec'
            )
            exec(byte_code, self.restricted_globals, self.loc)
        except Exception:
            raise SafePythonCompilerException(traceback.format_exc()) 
    
    def exec(self, func_name, *args, **kwargs):
        def _exec():
            with self._Patcher(self) as p:
                return self.loc[func_name](*args, **kwargs)

        try:

            return func_timeout(self._exec_timeout, _exec)
            
        except Exception:
            if '_stopThread\n    self._stderr = open(os.devnull, \'w\')' in traceback.format_exc():
                raise SafePythonCompilerException('{} execution timed out!'.format(func_name))
            else:
                raise  SafePythonCompilerException(traceback.format_exc())





