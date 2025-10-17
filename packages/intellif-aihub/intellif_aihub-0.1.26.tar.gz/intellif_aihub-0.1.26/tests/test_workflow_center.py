from __future__ import annotations

import unittest
import uuid
from time import sleep

from src.aihub.client import Client
from src.aihub.models.workflow_center import *

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ5MDY2ODUwODAsImlhdCI6MTc1MzA4NTA4MCwidWlkIjoxMH0.89bQ66BJDGoCzwxuxugRRt9acPFKEVmgqXMZX7ApnhM"


class TestWorkflowCenter(unittest.TestCase):
    def test_pipeline(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        pipe_name = f"sdk_pipeline_{uuid.uuid4().hex[:6]}"
        p_id = client.workflow_center.create_pipeline(
            CreatePipelineRequest(
                pipeline_name=pipe_name,
                version_name="09c4c9fd-14ae-4840-9173-63bb7d4ad49d",
                description="SDK 单测创建",
                nodes=[
                    Node(
                        command="echo 123",
                        depends_on=[],
                        image="ubuntu:latest",
                        name="task1",
                        position=[200, 100, 220, 50],
                        retry_cnt=0,
                        sku_cnt=1,
                        task_type="compute",
                        uuid="50b4b702-1f31-40e0-a3b5-17c62f97d143",
                    )
                ],
            )
        )
        self.assertGreater(p_id, 0)

        plist = client.workflow_center.list_pipelines(ListPipelinesRequest(name=pipe_name))
        self.assertTrue(any(p.id == p_id for p in plist.data))

        p_detail = client.workflow_center.get_pipeline(p_id)
        self.assertEqual(p_detail.name, pipe_name)

        brief = client.workflow_center.select_pipelines(pipe_name)
        self.assertTrue(any(b.id == p_id for b in brief))

        users = client.workflow_center.select_pipeline_users()
        self.assertIsInstance(users, list)

        client.workflow_center.delete_pipeline(p_id)

    def test_pipeline_version(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        pipe_name = f"sdk_pipeline_{uuid.uuid4().hex[:6]}"
        p_id = client.workflow_center.create_pipeline(
            CreatePipelineRequest(
                pipeline_name=pipe_name,
                version_name="09c4c9fd-14ae-4840-9173-63bb7d4ad49d",
                description="SDK 单测创建",
                nodes=[
                    Node(
                        command="echo 123",
                        depends_on=[],
                        image="ubuntu:latest",
                        name="task1",
                        # position=[200, 100, 220, 50],
                        retry_cnt=0,
                        sku_cnt=1,
                        task_type="compute",
                        uuid=str(uuid.uuid4()),
                    )
                ],
            )
        )
        self.assertGreater(p_id, 0)

        v2_id = client.workflow_center.create_pipeline_version(
            CreatePipelineVersionRequest(
                pipeline_id=p_id,
                version_name="v2",
                description="SDK 单测创建",
                nodes=[
                    Node(
                        command="echo 123",
                        depends_on=[],
                        image="ubuntu:latest",
                        name="task1",
                        # position=[200, 100, 220, 50],
                        retry_cnt=0,
                        sku_cnt=1,
                        task_type="compute",
                        uuid=str(uuid.uuid4()),
                    )
                ],
            )
        )
        self.assertGreater(v2_id, 0)

        v_lists = client.workflow_center.list_pipeline_versions(ListPipelineVersionsRequest(pipeline_id=p_id))
        self.assertTrue(any(v.id == v2_id for v in v_lists.data))

        v_detail = client.workflow_center.get_pipeline_version(v2_id)
        self.assertEqual(v_detail.name, "v2")

        v_briefs = client.workflow_center.select_pipeline_versions(SelectPipelineVersionsRequest(pipeline_id=p_id))
        self.assertTrue(any(v.id == v2_id for v in v_briefs))

        params = client.workflow_center.get_pipeline_version_input_params(291)
        self.assertIsInstance(params, list)

        client.workflow_center.migrate_pipeline_versions(MigratePipelineVersionsRequest(start_id=v2_id, end_id=v2_id, ))

        client.workflow_center.delete_pipeline_version(v2_id)

        client.workflow_center.delete_pipeline(p_id)

    def test_run(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        pipe_name = f"sdk_pipe_{uuid.uuid4().hex[:6]}"
        p_id = client.workflow_center.create_pipeline(
            CreatePipelineRequest(
                pipeline_name=pipe_name,
                version_name="V1",
                nodes=[
                    Node(
                        uuid=str(uuid.uuid4()),
                        name="task1",
                        task_type="compute",
                        position=[0, 0, 100, 60],
                        depends_on=[],
                        command="echo 123; sleep 5m",
                        image="ubuntu:latest",
                        sku_cnt=1,
                        retry_cnt=0,
                    )
                ],
            )
        )

        v_id = client.workflow_center.create_pipeline_version(
            CreatePipelineVersionRequest(
                pipeline_id=p_id,
                version_name="v2",
                nodes=[
                    Node(
                        uuid=str(uuid.uuid4()),
                        name="task1",
                        task_type="compute",
                        position=[0, 0, 100, 60],
                        depends_on=[],
                        command="echo 123; sleep 5m",
                        image="ubuntu:latest",
                        sku_cnt=1,
                        retry_cnt=0,
                    )
                ],
            )
        )

        run_name = f"sdk_run_{uuid.uuid4().hex[:6]}"
        run_id = client.workflow_center.create_run(
            CreateRunRequest(
                pipeline_id=p_id,
                pipeline_version_id=v_id,
                name=run_name,
                project_id=1,
                node_virtual_clusters=[
                    NodeVirtualClusterSetting(
                        virtual_cluster_id=289,
                        nodes=["task1"]
                    )
                ]
            )
        )
        self.assertGreater(run_id, 0)

        sleep(10)

        run_list = client.workflow_center.list_runs(ListRunsRequest(name=run_name))
        self.assertTrue(any(r.id == run_id for r in run_list.data))

        run_detail = client.workflow_center.get_run(run_id)
        self.assertEqual(run_detail.name, run_name)

        if run_detail.task_nodes:
            pod_name = run_detail.task_nodes[0].pod_name
            logs = client.workflow_center.get_run_task_logs(run_id, pod_name)
            self.assertIsInstance(logs.log, str)

            pod_info = client.workflow_center.get_run_task_pod(run_id, pod_name)
            self.assertTrue(pod_info.pod)

            events = client.workflow_center.get_run_task_events(run_id, pod_name)
            self.assertIsInstance(events.events, str)

        client.workflow_center.stop_run(run_id)

        client.workflow_center.resubmit_run(run_id)

        users = client.workflow_center.select_run_users()
        self.assertIsInstance(users, list)

        client.workflow_center.delete_pipeline_version(v_id)
        client.workflow_center.delete_pipeline(p_id)
