# -*- coding: utf-8 -*-
"""
OpenAPI 文档生成与 Apifox 同步工具。

两种模式：
1. 直接解析模式：从 Flask url_map + docstring 生成 OpenAPI 3.0（无需 flasgger）
2. Flasgger 模式：传入 flasgger 的 swagger_spec，提取完整元数据（参数类型、definitions）

使用示例：
    from flask_frame.openapi import generate_openapi, sync_to_apifox

    # 直接解析（无需 flasgger）
    spec = generate_openapi(app, title="My API")

    # Flasgger 模式同步（需要 flasgger）
    from flasgger import Swagger
    swagger = Swagger(app)
    with app.app_context():
        swagger_spec = swagger.get_apispecs()
    sync_to_apifox(app, token="xxx", project_id="xxx", swagger_spec=swagger_spec)
"""
import json
import os
import re
import inspect
import hashlib
from typing import Any

__all__ = ["generate_openapi", "sync_to_apifox"]


def _parse_docstring(func) -> dict[str, Any]:
    """
    解析视图函数的 docstring，提取 summary、description、参数说明。

    支持 Google 风格：
        summary 一句话描述
        更详细的 description

        Args:
            name (str): 参数说明
            page (int, optional): 页码，默认 1

        Returns:
            dict: 返回说明

    Returns:
        dict: {"summary": ..., "description": ..., "params": [...]}
    """
    doc = inspect.getdoc(func)
    if not doc:
        return {"summary": "", "description": "", "params": []}

    lines = doc.strip().split("\n")
    summary = lines[0].strip()
    description = ""
    params = []

    # 提取 Args 段落
    in_args = False
    for line in lines[1:]:
        stripped = line.strip()

        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if stripped and not stripped.startswith(" ") and not line.startswith(" "):
                # 遇到新的顶级段落，结束 Args
                in_args = False
            else:
                # 解析参数行：name (type): description  或  name: description
                match = re.match(
                    r"(\w+)\s*(?:\([^)]*\))?\s*[:：]\s*(.+)", stripped
                )
                if match:
                    params.append({
                        "name": match.group(1),
                        "description": match.group(2).strip(),
                    })

    # 非 Args 段落的非首行内容作为 description
    desc_lines = []
    in_args = False
    for line in lines[1:]:
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if stripped.lower().startswith("returns:"):
            break
        if not in_args and stripped:
            desc_lines.append(stripped)
    description = "\n".join(desc_lines)

    return {"summary": summary, "description": description, "params": params}


def _build_paths(app, filter_prefix: str | None = None) -> dict[str, dict]:
    """
    从 Flask app 的 url_map 构建 OpenAPI paths 对象。

    Args:
        app: Flask 应用实例。
        filter_prefix: 路径前缀过滤，仅包含以此前缀开头的路由。

    Returns:
        dict: OpenAPI paths 字典。
    """
    paths: dict[str, dict] = {}

    for rule in app.url_map.iter_rules():
        # 跳过静态文件和内部路由
        if rule.endpoint in ("static",) or rule.endpoint.startswith("flasgger"):
            continue

        path = rule.rule
        if filter_prefix and not path.startswith(filter_prefix):
            continue

        # 将 Flask 路径参数 <name> 转为 OpenAPI {name}
        openapi_path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", path)

        methods = [m for m in rule.methods if m not in ("HEAD", "OPTIONS")]
        if not methods:
            continue

        view_func = app.view_functions.get(rule.endpoint)
        doc_info = _parse_docstring(view_func) if view_func else {}

        # 从路由参数推断路径参数类型
        path_params = []
        for arg in rule.arguments:
            converter = rule._converters.get(arg)
            param_type = "string"
            if converter:
                type_map = {"int": "integer", "float": "number"}
                param_type = type_map.get(getattr(converter, "type", ""), "string")
            path_params.append({
                "name": arg,
                "in": "path",
                "required": True,
                "schema": {"type": param_type},
            })

        # 从 docstring 的 Args 段落补充 query 参数
        query_params = []
        for p in doc_info.get("params", []):
            query_params.append({
                "name": p["name"],
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "description": p["description"],
            })

        parameters = path_params + query_params

        path_item: dict[str, Any] = {}
        for method in methods:
            operation: dict[str, Any] = {
                "summary": doc_info.get("summary", f"{method} {openapi_path}"),
                "tags": [_get_tag(rule.endpoint)],
                "responses": {
                    "200": {"description": "成功"},
                    "500": {"description": "服务器错误"},
                },
            }
            if doc_info.get("description"):
                operation["description"] = doc_info["description"]
            if parameters:
                operation["parameters"] = parameters

            path_item[method.lower()] = operation

        paths[openapi_path] = path_item

    return paths


def _get_tag(endpoint: str) -> str:
    """从 endpoint 名称提取 tag（取第一段作为分组）。"""
    parts = endpoint.split(".")
    return parts[0] if len(parts) > 1 else "default"


def _extract_from_swagger(
    app,
    swagger_spec: dict,
    modules: list[str] | None = None,
    filter_prefix: str | None = None,
) -> dict:
    """
    从 flasgger 的 swagger spec 提取 API 信息（与 lms_service 逻辑一致）。

    Args:
        app: Flask 应用实例。
        swagger_spec: flasgger 生成的 Swagger 2.0 spec（swagger.get_apispecs()）。
        modules: 按模块名过滤（endpoint 前缀），None 表示全部。
        filter_prefix: 按路径前缀过滤。

    Returns:
        dict: 包含 paths 和 definitions 的 Swagger 2.0 格式 spec。
    """
    result = {
        "swagger": "2.0",
        "info": {"title": "API", "version": "1.0.0"},
        "paths": {},
        "definitions": {},
    }

    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static" or rule.endpoint.startswith("flasgger"):
            continue

        # 按模块过滤：endpoint 格式为 "module.name"
        endpoint_parts = rule.endpoint.split(".")
        if modules:
            if len(endpoint_parts) < 2 or endpoint_parts[0] not in modules:
                continue

        path = rule.rule
        if filter_prefix and not path.startswith(filter_prefix):
            continue

        methods = [m for m in rule.methods if m in ("GET", "POST", "PUT", "DELETE", "PATCH")]
        if not methods:
            continue

        # 从 swagger spec 获取对应的 API 信息
        swagger_path = swagger_spec.get("paths", {}).get(path, {})

        if path not in result["paths"]:
            result["paths"][path] = {}

        for method in methods:
            method_lower = method.lower()
            swagger_method = swagger_path.get(method_lower, {})

            # 跳过没有文档说明的接口（无 summary、description、parameters）
            has_summary = swagger_method.get("summary") and swagger_method["summary"] != f"{method} {path}"
            has_desc = bool(swagger_method.get("description"))
            has_params = bool(swagger_method.get("parameters"))
            if not has_summary and not has_desc and not has_params:
                continue

            method_spec = {
                "summary": swagger_method.get("summary", f"{method} {path}"),
                "description": swagger_method.get("description", ""),
                "tags": swagger_method.get("tags", [endpoint_parts[0] if len(endpoint_parts) > 1 else "default"]),
                "responses": swagger_method.get("responses", {}),
            }
            if "parameters" in swagger_method:
                method_spec["parameters"] = swagger_method["parameters"]

            result["paths"][path][method_lower] = method_spec

    # 提取 definitions（模型定义）
    for name, schema in swagger_spec.get("definitions", {}).items():
        result["definitions"][name] = schema

    return result


def generate_openapi(
    app,
    title: str = "API",
    version: str = "1.0.0",
    description: str = "",
    filter_prefix: str | None = None,
    group_by: str | None = None,
    output_dir: str | None = None,
) -> dict | dict[str, dict]:
    """
    从 Flask 应用生成 OpenAPI 3.0 规范。

    Args:
        app: 已初始化路由的 Flask 应用实例。
        title: API 标题。
        version: API 版本号。
        description: API 描述。
        filter_prefix: 仅生成以此路径前缀开头的路由（如 "/api/v1"）。
        group_by: 分组方式。"blueprint" 按蓝图前缀拆分为多个文件，None 生成单个文件。
        output_dir: 输出目录。指定时自动保存 JSON 文件。

    Returns:
        单文件模式返回 dict（OpenAPI 3.0 规范）。
        分组模式返回 dict[str, dict]（键为蓝图名，值为规范）。
    """
    base_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
        },
        "paths": {},
    }
    if description:
        base_spec["info"]["description"] = description

    if group_by == "blueprint":
        # 按蓝图分组
        tag_groups: dict[str, dict[str, dict]] = {}
        all_paths = _build_paths(app, filter_prefix)

        for path, path_item in all_paths.items():
            for method, operation in path_item.items():
                tag = operation.get("tags", ["default"])[0]
                if tag not in tag_groups:
                    tag_groups[tag] = {}
                if path not in tag_groups[tag]:
                    tag_groups[tag][path] = {}
                tag_groups[tag][path][method] = operation

        result = {}
        for tag, paths in tag_groups.items():
            spec = {**base_spec, "info": {**base_spec["info"], "title": f"{title} - {tag}"}, "paths": paths}
            result[tag] = spec

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            for tag, spec in result.items():
                file_path = os.path.join(output_dir, f"{tag}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(spec, f, ensure_ascii=False, indent=2)

        return result
    else:
        # 单文件模式
        spec = {**base_spec, "paths": _build_paths(app, filter_prefix)}

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, "openapi.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(spec, f, ensure_ascii=False, indent=2)

        return spec


def _compute_hash(data: Any) -> str:
    """计算数据的 SHA-256 哈希，用于增量同步对比。"""
    normalized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _load_snapshot(snapshot_dir: str) -> dict:
    """加载增量同步快照。"""
    hash_path = os.path.join(snapshot_dir, "path_hashes.json")
    if os.path.exists(hash_path):
        with open(hash_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_snapshot(snapshot_dir: str, data: dict) -> None:
    """保存增量同步快照。"""
    os.makedirs(snapshot_dir, exist_ok=True)
    hash_path = os.path.join(snapshot_dir, "path_hashes.json")
    with open(hash_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sync_to_apifox(
    app,
    token: str,
    project_id: str,
    title: str = "API",
    version: str = "1.0.0",
    description: str = "",
    filter_prefix: str | None = None,
    modules: list[str] | None = None,
    swagger_spec: dict | None = None,
    snapshot_dir: str | None = None,
    force: bool = False,
) -> bool:
    """
    生成 API 规范并同步到 Apifox，支持增量同步。

    两种模式：
    - Flasgger 模式：传入 swagger_spec（flasgger.get_apispecs()），提取完整元数据。
    - 直接解析模式：不传 swagger_spec，从 url_map + docstring 生成（降级）。

    Args:
        app: 已初始化路由的 Flask 应用实例。
        token: Apifox API Token（从 Apifox 项目设置 → API 认证 获取）。
        project_id: Apifox 项目 ID（从项目设置 → 基本信息获取）。
        title: API 标题。
        version: API 版本号。
        description: API 描述。
        filter_prefix: 仅同步以此路径前缀开头的路由。
        modules: 按模块名过滤（仅 flasgger 模式生效），如 ["inquiry", "quotation"]。
        swagger_spec: flasgger 生成的 Swagger 2.0 spec。传入时使用 flasgger 数据，否则降级为直接解析。
        snapshot_dir: 增量快照目录，默认为当前工作目录下的 .sync_snapshot。
        force: 强制全量同步，忽略增量检测。

    Returns:
        bool: 同步是否成功。
    """
    import requests

    # 根据是否有 swagger_spec 选择生成方式
    if swagger_spec is not None:
        extracted = _extract_from_swagger(app, swagger_spec, modules=modules, filter_prefix=filter_prefix)
        push_spec = extracted
    else:
        push_spec = generate_openapi(app, title=title, version=version, description=description, filter_prefix=filter_prefix)

    paths = push_spec.get("paths", {})
    definitions = push_spec.get("definitions", {})

    # 增量同步检测
    if snapshot_dir is None:
        snapshot_dir = os.path.join(os.getcwd(), ".sync_snapshot")

    if not force:
        last_hashes = _load_snapshot(snapshot_dir)
        new_hashes = {}
        changed_paths = {}

        for path, methods in paths.items():
            h = _compute_hash(methods)
            new_hashes[path] = h
            if last_hashes.get(path) != h:
                changed_paths[path] = methods

        deleted = set(last_hashes.keys()) - set(paths.keys()) - {"__definitions__"}

        # 检测 definitions 变化
        defs_hash = _compute_hash(definitions)
        last_defs_hash = last_hashes.get("__definitions__", "")
        defs_changed = defs_hash != last_defs_hash

        if not changed_paths and not deleted and not defs_changed:
            print(f"总接口数: {len(paths)}")
            print("检测到变更: 0")
            print("跳过同步")
            return True

        if defs_changed and not changed_paths and not deleted:
            print(f"总接口数: {len(paths)}")
            print("检测到变更: definitions 变化")
            print(f"推送到 Apifox: 全量 ({len(paths)} 个接口)")
            incremental = False
        else:
            print(f"总接口数: {len(paths)}")
            label = f"检测到变更: {len(changed_paths)} 个接口"
            if deleted:
                label += f"，{len(deleted)} 个删除"
            if defs_changed:
                label += "，definitions 变化"
            print(label)
            push_count = len(changed_paths) + len(deleted)
            print(f"推送到 Apifox: {push_count} 个接口")
            incremental = True

        new_hashes["__definitions__"] = defs_hash
    else:
        print(f"总接口数: {len(paths)}")
        print("强制全量同步")
        print(f"推送到 Apifox: {len(paths)} 个接口")
        incremental = False
        new_hashes = {p: _compute_hash(m) for p, m in paths.items()}
        new_hashes["__definitions__"] = _compute_hash(definitions)

    # 调用 Apifox API
    url = f"https://api.apifox.com/v1/projects/{project_id}/import-openapi?locale=zh-CN"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Apifox-Api-Version": "2024-03-28",
        "Content-Type": "application/json",
    }

    # 增量模式只发变更的 paths + definitions，全量模式发完整 spec
    if incremental:
        minimal_paths = dict(changed_paths)
        for p in deleted:
            minimal_paths[p] = {}
        push_input = {
            "swagger": "2.0",
            "info": push_spec.get("info", {}),
            "paths": minimal_paths,
            "definitions": definitions,
        }
    else:
        push_input = push_spec

    payload = {
        "input": json.dumps(push_input, ensure_ascii=False),
        "options": {
            "endpointOverwriteBehavior": "OVERWRITE_EXISTING",
            "schemaOverwriteBehavior": "OVERWRITE_EXISTING",
            "updateFolderOfChangedEndpoint": True,
            "deleteUnmatchedResources": not incremental,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            counters = result.get("data", {}).get("counters", {})
            created = counters.get("endpointCreated", 0)
            updated = counters.get("endpointUpdated", 0)
            failed = counters.get("endpointFailed", 0)
            print(f"同步成功！创建: {created}, 更新: {updated}, 失败: {failed}")

            # 保存快照
            _save_snapshot(snapshot_dir, new_hashes)
            return True
        else:
            print(f"同步失败，状态码: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return False
