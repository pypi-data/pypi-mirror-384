# -*- coding: utf-8 -*-
import importlib

# 想延迟加载的子模块列表
_LAZY_SUBMODULES = ['ai', 'cv', 'data', 'dataset', 'loanlib']

# 需要在顶层暴露的函数映射：顶层名字 -> (子模块名, 子模块内函数名)
_EXPOSED_FUNCS = {
    'fast_loadenv_then_append_path': ('loanlib', 'fast_loadenv_then_append_path'),
    'o_d': ('misc', 'o_d'),

    # 如果以后想暴露更多函数，继续添加
    # 'other_func': ('loanlib', 'other_func'),
}

# 缓存已加载的子模块
_loaded_submodules = {}

def __getattr__(name):
    # 先检查是否是暴露的函数
    if name in _EXPOSED_FUNCS:
        mod_name, func_name = _EXPOSED_FUNCS[name]
        if mod_name not in _loaded_submodules:
            _loaded_submodules[mod_name] = importlib.import_module(f'.{mod_name}', __name__)
        func = getattr(_loaded_submodules[mod_name], func_name)
        # 缓存到globals，避免重复导入
        globals()[name] = func
        return func

    # 再检查是否是延迟加载的子模块
    if name in _LAZY_SUBMODULES:
        if name not in _loaded_submodules:
            _loaded_submodules[name] = importlib.import_module(f'.{name}', __name__)
        module = _loaded_submodules[name]
        globals()[name] = module
        return module

    raise AttributeError(f"module {__name__} has no attribute {name}")

def whoami():
    """Who am I?"""
    return "I am Elinor, a Python package for data processing and analysis."