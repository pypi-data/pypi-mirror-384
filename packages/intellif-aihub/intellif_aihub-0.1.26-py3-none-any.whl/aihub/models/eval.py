# !/usr/bin/env python
# -*-coding:utf-8 -*-
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BaseEvalReq(BaseModel):
    """评测任务基础请求模型"""

    run_id: str = Field(description="运行ID")
    type: str = Field(description="评测类型，支持 'llm' 和 'cv'")
    prediction_artifact_path: str = Field(description="推理产物的路径")
    user_id: int = Field(0, description="用户ID，默认0")


class ClientType(Enum):
    """客户端类型枚举"""

    Workflow = "workflow"
    sdk = "sdk"


class CreateLLMEvalReq(BaseEvalReq):
    """创建LLM类型评测任务请求"""

    type: str = Field(default="llm", description="评测类型，固定为 'llm'")
    dataset_id: int = Field(description="数据集ID")
    dataset_version_id: int = Field(description="数据集版本ID")
    evaled_artifact_path: str = Field(description="评测结果产物的路径")
    report: Dict = Field(description="评测报告")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = {"use_enum_values": True}


class CreateCVEvalReq(BaseEvalReq):
    """创建CV类型评测任务请求"""

    type: str = Field(default="cv", description="评测类型，固定为 'cv'")
    metrics_artifact_path: str = Field(description="指标产物的路径")
    ground_truth_artifact_path: str = Field(description="真实标签产物的路径")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = {"use_enum_values": True}


class EvalRun(BaseModel):
    """评测任务的运行实体"""

    id: int = Field(description="评测的运行ID")
    name: str = Field(description="评测名称")
    description: str = Field(description="评测描述")
    user_id: int = Field(description="用户ID")
    model_id: int = Field(description="模型ID")
    model_name: str = Field(description="模型名称")
    dataset_id: int = Field(description="数据集ID")
    dataset_version_id: int = Field(description="数据集版本ID")
    dataset_name: str = Field(description="数据集名称")
    status: str = Field(description="状态")
    prediction_artifact_path: str = Field(description="推理产物路径")
    evaled_artifact_path: str = Field(description="评测结果产物路径")
    run_id: str = Field(description="运行ID")
    dataset_summary: Dict = Field(default_factory=dict, description="数据集摘要")
    metrics_summary: Dict = Field(default_factory=dict, description="指标摘要")
    viz_summary: Dict = Field(default_factory=dict, description="可视化摘要")
    eval_config: Optional[Dict] = Field(default=None, description="评测配置")
    created_at: int = Field(description="创建时间")
    updated_at: int = Field(description="更新时间")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = {"use_enum_values": True, "protected_namespaces": ()}


class CreateEvalResp(BaseModel):
    """创建评测任务的返回结果"""

    eval_run: EvalRun = Field(alias="eval_run", description="评测运行信息")


class ListEvalReq(BaseModel):
    """列出评测任务请求"""

    page_size: int = Field(20, description="页面大小")
    page_num: int = Field(1, description="页码")
    status: Optional[str] = Field(None, description="状态过滤")
    name: Optional[str] = Field(None, description="名称过滤")
    model_id: Optional[int] = Field(None, description="模型ID过滤")
    dataset_id: Optional[int] = Field(None, description="数据集ID过滤")
    dataset_version_id: Optional[int] = Field(None, description="数据集版本ID过滤")
    run_id: Optional[str] = Field(None, description="运行ID过滤")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    model_ids: Optional[str] = Field(None, description="模型ID列表过滤")
    dataset_ids: Optional[str] = Field(None, description="数据集ID列表过滤")
    dataset_version_ids: Optional[str] = Field(None, description="数据集版本ID列表过滤")
    model_config = {"use_enum_values": True, "protected_namespaces": ()}


class ListEvalResp(BaseModel):
    """列出评测任务响应"""

    total: int = Field(description="总数")
    page_size: int = Field(description="页面大小")
    page_num: int = Field(description="页码")
    data: List[EvalRun] = Field(description="评测运行列表")


class GrantPermissionReq(BaseModel):
    """授权权限请求"""

    user_ids: list[int] = Field(description="用户ID数组")
