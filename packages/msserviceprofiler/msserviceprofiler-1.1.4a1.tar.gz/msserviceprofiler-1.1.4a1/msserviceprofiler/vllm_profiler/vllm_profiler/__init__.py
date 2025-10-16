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
import os
import importlib.metadata as importlib_metadata

from .utils import logger, set_log_level
from .module_hook import apply_hooks
from .dynamic_hook import apply_hooks_with_config

set_log_level("info")  # Default is info, put here for user changes


def _parse_version_tuple(version_str):
    parts = version_str.split("+")[0].split("-")[0].split(".")
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            break
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def _auto_detect_v1_default():
    """Auto decide default V1 usage based on installed vLLM version.

    Heuristic: for newer vLLM (>= 0.9.2) default to V1, otherwise V0.
    If version can't be determined, fall back to V0 for safety.
    """
    try:
        vllm_version = importlib_metadata.version("vllm")
        major, minor, patch = _parse_version_tuple(vllm_version)
        use_v1 = (major, minor, patch) >= (0, 9, 2)
        logger.info(
            f"VLLM_USE_V1 not set, auto-detected via vLLM {vllm_version}: default {'1' if use_v1 else '0'}"
        )
        return "1" if use_v1 else "0"
    except Exception as e:
        logger.info("VLLM_USE_V1 not set and vLLM version unknown; default to 0 (V0)")
        return "0"


_env_v1 = os.environ.get('VLLM_USE_V1')
VLLM_USE_V1 = _env_v1 if _env_v1 is not None else _auto_detect_v1_default()


def _find_config_path():
    """Find profiling config file with priority:
    1) vllm_ascend installation directory: vllm_ascend/profiling_config/service_profiling_symbols.yaml
    2) This project: <this>/config/service_profiling_symbols.yaml
    """
    # 1) vllm_ascend installation path
    try:
        # Try common distribution/package names
        for dist_name in ('vllm-ascend', 'vllm_ascend'):
            try:
                dist = importlib_metadata.distribution(dist_name)  # type: ignore
            except Exception:
                continue
            # Resolve the package directory using locate_file on the package name
            try:
                ascend_pkg_dir = dist.locate_file('vllm_ascend')  # type: ignore
                ascend_dir = os.fspath(ascend_pkg_dir)
            except Exception:
                ascend_dir = None
            if ascend_dir and os.path.isdir(ascend_dir):
                candidate = os.path.join(ascend_dir, 'profiling_config', 'service_profiling_symbols.yaml')
                if os.path.isfile(candidate):
                    logger.debug(f"Using profiling symbols from vllm_ascend distribution: {candidate}")
                    return candidate
    except Exception:
        pass

    # 2) local project config path
    local_candidate = os.path.join(os.path.dirname(__file__), 'config', 'service_profiling_symbols.yaml')
    if os.path.isfile(local_candidate):
        logger.debug(f"Using profiling symbols from local project: {local_candidate}")
        return local_candidate

    return None


def register_service_profiler():
    init_service_profiler()


def init_service_profiler():
    # 优先检查是否启用打点：必须显式设置 SERVICE_PROF_CONFIG_PATH 才启用
    if not os.environ.get('SERVICE_PROF_CONFIG_PATH'):
        return

    # 按版本导入内置 hookers（供配置引用），并准备回退逻辑
    if VLLM_USE_V1 == "0":
        logger.debug("Initializing service profiler with vLLM V0 interface")
        from .vllm_v0 import batch_hookers, kvcache_hookers, model_hookers, request_hookers  # noqa: F401
    elif VLLM_USE_V1 == "1":
        logger.debug("Initializing service profiler with vLLM V1 interface")
        from .vllm_v1 import batch_hookers, kvcache_hookers, model_hookers, request_hookers  # noqa: F401
    else:
        logger.error(f"unknown vLLM interface version: VLLM_USE_V1={VLLM_USE_V1}")
        return

    cfg_path = _find_config_path()
    if cfg_path:
        logger.debug(f"Applying hooks with symbols config: {cfg_path}")
        successfully_load = apply_hooks_with_config(cfg_path, prefer_builtin=True)
        if successfully_load:
            logger.debug("Successfully apply hooks with config")
        else:
            logger.debug("hooks applied failed; falling back to default hooks")
            apply_hooks()  # 配置不可用时回退到默认打点
    else:
        logger.error(f"Failed to load symbols config file!")
