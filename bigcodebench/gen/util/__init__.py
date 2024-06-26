import time
import sys
import types
import unittest

from bigcodebench.eval.utils import (
    create_tempdir,
    reliability_guard,
    swallow_io,
    time_limit,
    safe_environment,
)


def trusted_exec(code, test_code, task_id, max_as_limit, max_data_limit, max_stack_limit):
    """Execute trusted code in place."""

    with create_tempdir():
        import os
        import shutil
        import builtins

        rmtree = shutil.rmtree
        rmdir = os.rmdir
        chdir = os.chdir
        module_name = "__test__"
        new_module = types.ModuleType(module_name)
        reliability_guard(max_as_limit, max_data_limit, max_stack_limit)
        # Set necessary attributes for the module
        new_module.__dict__.update({
            '__builtins__': builtins,
            '__file__': f"{module_name}.py",
            '__package__': None,
            '__doc__': None,
            'sys': sys,
            'os': os,
            'environ': os.environ,
        })

        # Combine the user code and the test code
        full_code = code + "\n" + test_code

        # Compile and execute the combined code within the new module
        exec(compile(full_code, f"{module_name}.py", 'exec'),
             new_module.__dict__)
        sys.modules[module_name] = new_module
        TestCases = getattr(new_module, 'TestCases')
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestCases)
        test_result = unittest.TestResult()
        start = time.time()
        with safe_environment(), swallow_io():
            suite.run(test_result)
        
        # Needed for cleaning up.
        shutil.rmtree = rmtree
        os.rmdir = rmdir
        os.chdir = chdir

        if len(test_result.failures + test_result.errors) > 0:
            return None
        return time.time() - start

def trusted_check_exec(code, inputs):
    """Check trusted_exec success."""
    try:
        with time_limit(seconds=120):
            trusted_exec(code, inputs)
    except Exception:
        return False
    return True
