# Copyright (c) 2025-2025 Huawei Technologies Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib
import inspect
from typing import Tuple, List, Optional, Callable, Dict, Any
from .utils import logger
from .module_hook import VLLMHookerBase, import_object_from_string, apply_hooks
from .registry import (
    clear_hook_registry,
    get_hook_registry,
    get_builtin_cache,
    set_builtin_cache
)    


class DynamicHooker(VLLMHookerBase):
    """用于在运行时基于配置注册的 Hooker。"""
    def __init__(self, hook_list: List[Tuple[str, str]], hook_func: Callable,
                 min_version: Optional[str], max_version: Optional[str], caller_filter: Optional[str]):
        super().__init__()
        self.vllm_version = (min_version, max_version)
        self.applied_hook_func_name = getattr(hook_func, "__name__", str(hook_func))
        self.hook_list = list(hook_list)
        self.caller_filter = caller_filter
        self.hook_func = hook_func

    def init(self):
        points = [import_object_from_string(import_path, func_path) for import_path, func_path in self.hook_list]
        self.do_hook(
            hook_points=points,
            profiler_func_maker=lambda ori_func: lambda *args, **kwargs: self.hook_func(ori_func, *args, **kwargs),
            pname=self.caller_filter,
        )


def register_dynamic_hook(hook_list: List[Tuple[str, str]], hook_func: Callable,
                          min_version: Optional[str] = None, max_version: Optional[str] = None,
                          caller_filter: Optional[str] = None):
    """注册一个基于配置文件的动态 Hooker"""
    hooker = DynamicHooker(hook_list, hook_func, min_version, max_version, caller_filter)
    hooker.register()
    return hooker


def make_default_time_hook(domain: str, name: str, attributes: Optional[List[Dict[str, Any]]] = None) -> Callable:
    """生成一个默认的耗时统计 hook 处理函数，并支持自定义属性采集。

    attributes 结构（列表，可选）：
      - source: "input" | "output"  # 原 when 重命名为 source
      - name: str  # 采集项名
      - expr: str  # 表达式，如 "len(kwargs['input_ids'])"、"str(args[0])"、"kwargs['any'].attr"
    """
    try:
        from ms_service_profiler import Profiler, Level
    except Exception:
        def _noop(original_func, *args, **kwargs):
            return original_func(*args, **kwargs)
        return _noop

    def _safe_eval_expr(expr: str, func_obj, this_obj, args_tuple, kwargs_dict, ret_val):
        """安全执行表达式，支持管道操作和 attr 操作"""
        def _attr(obj, attr_name):
            """获取对象属性"""
            return getattr(obj, attr_name, None)
        
        def _pipe_eval(expr_str):
            """处理管道表达式"""
            if '|' not in expr_str:
                # 没有管道，直接执行
                return _direct_eval(expr_str)
            
            # 分割管道操作
            parts = [part.strip() for part in expr_str.split('|')]
            if len(parts) < 2:
                return _direct_eval(expr_str)
            
            # 执行第一个表达式
            result = _direct_eval(parts[0])
            
            # 依次执行后续操作
            for part in parts[1:]:
                if part == 'str':
                    result = str(result)
                elif part == 'int':
                    result = int(result) if result is not None else None
                elif part == 'float':
                    result = float(result) if result is not None else None
                elif part == 'bool':
                    result = bool(result) if result is not None else None
                elif part == 'len':
                    result = len(result) if result is not None else None
                elif part.startswith('attr '):
                    # attr 操作：attr attribute_name
                    attr_name = part[5:].strip()
                    result = _attr(result, attr_name)
                else:
                    # 其他函数调用
                    try:
                        result = _direct_eval(f"{part}({repr(result)})")
                    except:
                        logger.warning(f"Unknown pipe operation: {part}")
                        return None
            
            return result
        
        def _direct_eval(expr_str):
            """直接执行表达式"""
            safe_builtins = {}
            # 解析函数形参名称，注入到可见作用域，便于直接使用 input_ids 等参数名
            named_params: Dict[str, Any] = {}
            try:
                sig = inspect.signature(func_obj)
                bound = sig.bind_partial(*args_tuple, **kwargs_dict)
                named_params = dict(bound.arguments)
            except Exception:
                named_params = {}
            # 提供 this（优先使用 self），以及常用内置与辅助函数
            self_obj = named_params.get("self", this_obj)
            safe_locals = {
                "this": self_obj,
                "args": args_tuple,
                "kwargs": kwargs_dict,
                "return": ret_val,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "attr": _attr,
            }
            # 将所有具名参数直接注入到可见作用域，允许表达式直接以参数名访问
            try:
                safe_locals.update({k: v for k, v in named_params.items() if k != "self"})
            except Exception:
                pass
            try:
                return eval(expr_str, {"__builtins__": safe_builtins}, safe_locals)
            except Exception as e:
                logger.warning(f"Direct eval failed: {expr_str}, err={e}")
                return None
        
        try:
            return _pipe_eval(expr)
        except Exception as e:
            logger.warning(f"Pipe eval failed: {expr}, err={e}")
            return None

    def _default(original_func, *args, **kwargs):
        prof = Profiler(Level.INFO).domain(domain).span_start(name)
        ret = original_func(*args, **kwargs)

        if isinstance(attributes, list):
            for item in attributes:
                attr_name = item.get("name")
                expr = item.get("expr")
                if not attr_name or not expr:
                    continue
                # 在 expr 中直接使用参数名或 return 来表示数据来源
                val = _safe_eval_expr(expr, original_func, args[0] if len(args) > 0 else None, args, kwargs, ret)
                if val is not None:
                    prof.attr(attr_name, val)

        prof.span_end()
        return ret

    return _default


class ConfigParser:
    """配置解析器，负责解析YAML配置文件"""
    
    def __init__(self):
        self._yaml_available = self._check_yaml_availability()
    
    def _check_yaml_availability(self):
        try:
            import yaml  # type: ignore
            return True
        except ImportError:
            logger.warning(f"PyYAML is not installed, ignore YAML configuration")
            return False
    
    def parse(self, path: str) -> Optional[Dict[str, Any]]:
        """解析YAML配置文件"""
        if not self._yaml_available:
            return None
            
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data
        except FileNotFoundError:
            logger.warning(f"Configuration file does not exist: {path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load YAML: {e}")
            return None


class ConfigExtractor:
    """配置提取器，负责从配置数据中提取hook配置"""
    
    def extract(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从配置数据中提取hook配置列表
        只支持纯数组格式：顶层直接是列表，每个项目包含 symbol 字段
        """
        if isinstance(data, list):
            return data
        logger.warning("Configuration file should be a list of hook configurations")
        return []


class HookPointNormalizer:
    """Hook点标准化器，负责将配置项转换为标准格式"""
    def normalize(self, item: Dict[str, Any]) -> List[Tuple[str, str]]:
        """期望格式：
        - symbol: "abc.xyz:DummyClass.dummy_method" 或 "abc.xyz:dummy_function"
        返回：[(import_path, attr_path)]，仅一个点位
        """
        symbol = item.get("symbol")
        if isinstance(symbol, str) and ":" in symbol:
            mod, attr = symbol.split(":", 1)
            mod = mod.strip()
            attr = attr.strip()
            if mod and attr:
                return [(mod, attr)]

        # 不支持 points 列表（已废弃）
        return []


class HandlerResolver:
    """Handler解析器：有可导入的自定义 handler 则用之，否则使用 timer"""
    
    def __init__(self, prefer_builtin: bool = True):
        self.prefer_builtin = prefer_builtin
    
    def resolve(self, item: Dict[str, Any], points: List[Tuple[str, str]]) -> Callable:
        """根据配置解析handler函数"""
        domain = item.get("domain") or "Custom"
        name = item.get("name") or (points[0][1] if points else "custom")
        attributes = item.get("attributes")  # 新增：自定义属性采集配置
        handler_val = item.get("handler")
        handler_lower = handler_val.lower() if isinstance(handler_val, str) else None

        # 显式 timer
        if handler_lower == "timer" or handler_val is None:
            return make_default_time_hook(domain, name, attributes)

        # 自定义 import 形式
        if isinstance(handler_val, str) and ":" in handler_val:
            func = self._try_import(handler_val)
            if func is not None:
                return func
            logger.warning(f"Failed to import handler '{handler_val}', fallback to timer")
            return make_default_time_hook(domain, name, attributes)

        # 其他值（含 builtin）一律按 timer 处理
        return make_default_time_hook(domain, name, attributes)
    
    def _try_import(self, handler_val: str) -> Optional[Callable]:
        """尝试按 'pkg.mod:func' 导入自定义 handler，失败返回 None"""
        try:
            mod, func_name = handler_val.split(":", 1)
            mod_obj = importlib.import_module(mod)
            handler_func = getattr(mod_obj, func_name, None)
            return handler_func
        except Exception:
            return None


class ConfigApplier:
    """配置应用器，负责应用配置化的hook设置"""
    
    def __init__(self, prefer_builtin: bool = True):
        self.prefer_builtin = prefer_builtin
        self.parser = ConfigParser()
        self.extractor = ConfigExtractor()
        self.normalizer = HookPointNormalizer()
        self.resolver = HandlerResolver(prefer_builtin)
    
    def apply_config(self, config_path: str) -> bool:
        """加载并应用配置化的打点"""
        # 解析配置
        data = self.parser.parse(config_path)
        if not data:
            logger.info(f"Configuration file not found or cannot be parsed: {config_path}, skip configuration application")
            return False
        
        # 提取hook配置
        hooks_cfg = self.extractor.extract(data)
        if not hooks_cfg:
            logger.warning("No valid hook configuration found in configuration file")
            return False
        
        # 缓存当前已存在的（通常是内置）hookers，便于查找复用
        set_builtin_cache(list(get_hook_registry()))
        
        # 清空注册表，随后仅注册配置中声明的点位
        clear_hook_registry()
        
        # 处理每个配置项
        for item in hooks_cfg:
            self._process_config_item(item)
        
        # 应用当前注册表（仅动态注册的内容）
        apply_hooks()
        return True
    
    def _process_config_item(self, item: Dict[str, Any]):
        """处理单个配置项"""
        # 标准化hook点
        points = self.normalizer.normalize(item)
        if not points:
            return
        
        # 确定是否为custom
        is_custom = bool(item.get("__is_custom", False))
        
        # 确定版本约束
        if is_custom:
            min_v, max_v = None, None
        else:
            min_v, max_v = item.get("min_version"), item.get("max_version")
        
        # 获取caller filter
        caller = item.get("caller_filter")
        
        # 解析handler
        hook_func = self.resolver.resolve(item, points)
        
        # 注册动态hook
        register_dynamic_hook(points, hook_func, min_v, max_v, caller)


def apply_hooks_with_config(config_path: str, prefer_builtin: bool = True):
    """加载并应用配置化的打点"""
    applier = ConfigApplier(prefer_builtin)
    return applier.apply_config(config_path)
