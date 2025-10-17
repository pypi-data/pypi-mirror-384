# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""标签资源管理服务模块

封装 **tag‑resource‑management** 相关接口，提供两组下拉选项：

- **选择项目（Project）下拉列表**
- **选择虚拟集群（Virtual‑Cluster）下拉列表**
"""

from __future__ import annotations

from typing import List

import httpx

from ..exceptions import APIError
from ..models.common import APIWrapper
from ..models.tag_resource_management import (
    Project,
    ProjectListData,
    SelectVirtualClustersRequest,
    SelectVirtualClustersResponse,
    VirtualClusterBrief,
)

_BASE = "/tag-resource-management/api/v1"


class TagResourceManagementService:
    """标签资源管理服务"""

    def __init__(self, http: httpx.Client):
        self._project = _Project(http)
        self._virtual_cluster = _VirtualCluster(http)

    def select_projects(self) -> List[Project]:
        """获取全部项目下拉选项

        Returns:
            list[Project]: 项目列表，每项仅包含 `id` / `name`
        """
        return self._project.select_projects()

    def select_virtual_clusters(self, payload: SelectVirtualClustersRequest) -> List[VirtualClusterBrief]:
        """获取虚拟集群下拉选项

        Args:
            payload: 查询参数，包含用户 ID / 模块类型等过滤条件，详见 :class:`SelectVirtualClustersRequest`

        Returns:
            list[VirtualClusterBrief]: 过滤后的虚拟集群简要列表
        """
        return self._virtual_cluster.select(payload).data

    @property
    def project(self) -> _Project:
        return self._project

    @property
    def virtual_cluster(self) -> _VirtualCluster:
        return self._virtual_cluster


class _Project:
    def __init__(self, http: httpx.Client):
        self._http = http

    def select_projects(self) -> List[Project]:
        resp = self._http.get(f"{_BASE}/select-projects")
        wrapper = APIWrapper[ProjectListData].model_validate(resp.json())
        if wrapper.code != 0:
            raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        return wrapper.data.data


class _VirtualCluster:
    def __init__(self, http: httpx.Client):
        self._http = http

    def select(self, payload: SelectVirtualClustersRequest) -> SelectVirtualClustersResponse:
        resp = self._http.get(f"{_BASE}/select-clusters", params=payload.model_dump(by_alias=True, exclude_none=True))
        wrapper = APIWrapper[SelectVirtualClustersResponse].model_validate(resp.json())
        if wrapper.code != 0:
            raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        return wrapper.data
