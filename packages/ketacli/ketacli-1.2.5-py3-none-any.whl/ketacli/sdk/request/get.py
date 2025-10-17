from ..util import is_fuzzy_key, Template
from .asset_map import get_resources, get_request_path


def get_asset_by_id_request(asset_type, asset_id=None, lang=None, **kwargs):
    path, method, _ = get_request_path(asset_type, "get")
    kwargs.update({"asset_id": asset_id})
    old_path = path
    if asset_id is not None:
        path = Template(path).render(**kwargs)

        # 当通过字符串格式化方式未能获取到变化时，则将对象 id 拼到 url 后面
        if path == old_path:
            path = f"{path}/{asset_id}"

    custom_headers = {}
    if lang is not None and isinstance(lang, str):
        custom_headers["X-Pandora-Language"] = lang

    return {
        "path": path,
        "query_params": {},
        # list 操作用不到的内容
        "method": method,
        "data": {},
        "custom_headers": custom_headers,
    }
