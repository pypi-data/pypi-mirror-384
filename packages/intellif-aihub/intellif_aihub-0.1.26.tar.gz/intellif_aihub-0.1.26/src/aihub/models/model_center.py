from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ListModelCard(BaseModel):
    """模型卡片"""

    id: int = Field(alias="id", description="模型ID")
    name: str = Field(alias="name", description="名称")
    description: str = Field(alias="description", description="描述")
    creator_id: int = Field(alias="creator_id", description="创建人ID")
    creator_name: str = Field(alias="creator_name", description="创建人名称")
    created_at: int = Field(alias="created_at", description="创建时间戳")
    updated_at: int = Field(alias="updated_at", description="更新时间戳")
    tags: List[int] = Field(default_factory=list, alias="tags", description="标签ID集合")
    status: str = Field(alias="status", description="状态")
    is_public: bool = Field(alias="is_public", description="是否公开")

    @field_validator("tags", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        return [] if v is None else v

    model_config = ConfigDict(protected_namespaces=())


class ModelTreeNode(BaseModel):
    """模型树节点"""

    model_id: int = Field(alias="model_id", description="模型ID")
    name: str = Field(alias="name", description="名称")
    relationship: str = Field(alias="relationship", description="与基模型关系")

    model_config = ConfigDict(protected_namespaces=())


class ModelCardDetail(ListModelCard):
    """模型卡片详情"""

    readme_content: str = Field(alias="readme_content", description="README 内容")
    model_tree: Optional[List[ModelTreeNode]] = Field(default=None, alias="model_tree", description="模型树")
    base_model: Optional[ModelTreeNode] = Field(default=None, alias="base_model", description="基模型")
    file_storage_path: Optional[str] = Field(alias="file_storage_path", description="文件存储路径")

    model_config = ConfigDict(protected_namespaces=())


class ModelDb(BaseModel):
    """模型"""

    id: int = Field(description="ID")
    name: str = Field(description="名称")
    description: str = Field(description="描述")
    readme_content: str = Field(alias="readme_content", description="README")
    user_id: int = Field(alias="user_id", description="创建人ID")
    status: str = Field(description="状态")
    is_public: bool = Field(alias="is_public", description="是否公开")
    base_model_id: int = Field(alias="base_model_id", description="基模型ID")
    relation: str = Field(description="与基模型关系")
    object_cnt: int = Field(alias="object_cnt", description="对象数量")
    data_size: int = Field(alias="data_size", description="数据大小")
    object_storage_path: str = Field(alias="object_storage_path", description="对象存储路径")
    file_storage_path: str = Field(alias="file_storage_path", description="文件存储路径")
    parquet_index_path: str = Field(alias="parquet_index_path", description="Parquet 索引路径")
    csv_file_path: str = Field(alias="csv_file_path", description="CSV 文件路径")
    task_status_s3_path: str = Field(alias="task_status_s3_path", description="任务状态S3路径")
    created_at: int = Field(alias="created_at", description="创建时间戳")
    updated_at: int = Field(alias="updated_at", description="更新时间戳")


class ListModelsRequest(BaseModel):
    """查询模型列表请求"""

    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    name: Optional[str] = Field(default=None, alias="name", description="名称过滤")
    tags: Optional[str] = Field(default=None, alias="tags", description="标签过滤")
    model_ids: Optional[str] = Field(default=None, alias="model_ids", description="模型ID过滤")

    model_config = ConfigDict(protected_namespaces=())


class ListModelsResponse(BaseModel):
    """查询模型列表返回"""

    total: int = Field(alias="total", description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[ListModelCard] = Field(default_factory=list, alias="data", description="模型卡片列表")

    model_config = ConfigDict(protected_namespaces=())


class GetModelRequest(BaseModel):
    """查询模型详情请求"""

    id: int = Field(alias="id", description="模型ID")


class CreateModelRequest(BaseModel):
    """创建模型请求"""

    name: str = Field(alias="name", description="名称")
    description: Optional[str] = Field(default=None, alias="description", description="描述")
    tags: Optional[str] = Field(default=None, alias="tags", description="标签")
    is_public: bool = Field(alias="is_public", description="是否公开")
    readme_content: Optional[str] = Field(default=None, description="README 文本内容")


class CreateModelResponse(BaseModel):
    id: int = Field(alias="id", description="模型ID")


class EditModelRequest(BaseModel):
    """编辑模型请求"""

    name: Optional[str] = Field(default=None, alias="name", description="名称")
    description: Optional[str] = Field(default=None, alias="description", description="描述")
    is_public: Optional[bool] = Field(default=None, alias="is_public", description="是否公开")


class EditModelResponse(BaseModel):
    """编辑模型返回"""

    pass
