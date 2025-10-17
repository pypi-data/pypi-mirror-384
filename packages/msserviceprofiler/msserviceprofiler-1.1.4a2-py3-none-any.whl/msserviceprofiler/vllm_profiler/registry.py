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

# 全局注册表存储所有hookers
HOOK_REGISTRY = []
# 仅用于在基于配置的场景下，临时保存已导入的内置 Hooker 列表
BUILTIN_HOOKERS_CACHE = []


def clear_hook_registry():
    global HOOK_REGISTRY
    HOOK_REGISTRY = []


def clear_builtin_cache():
    global BUILTIN_HOOKERS_CACHE
    BUILTIN_HOOKERS_CACHE = []


def get_hook_registry():
    return HOOK_REGISTRY


def get_builtin_cache():
    return BUILTIN_HOOKERS_CACHE


def add_to_hook_registry(hooker):
    HOOK_REGISTRY.append(hooker)


def set_builtin_cache(cache):
    global BUILTIN_HOOKERS_CACHE
    BUILTIN_HOOKERS_CACHE = cache
