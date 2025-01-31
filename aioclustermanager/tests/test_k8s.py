import pytest
import asyncio

pytestmark = pytest.mark.asyncio
import time

async def test_get_deploy_k8s(kubernetes):
    # We clean up all the jobs on the namespace

    result = await kubernetes.get_nodes()
    assert len(result) > 0

    jobs_info = await kubernetes.list_deploys("aiocluster-test")
    assert jobs_info.total == 0

    await kubernetes.create_deploy(
        "aiocluster-test",  # namespace
        "test-deploy",  # jobid
        "nginx",  # image
        {
            "app": "nginx"
        }
    )

    deploy_info = await kubernetes.get_deploy("aiocluster-test", "test-deploy")
    assert deploy_info.id == "test-deploy"

    deploys_info = await kubernetes.list_deploys("aiocluster-test")
    assert deploys_info.total == 1

    await kubernetes.deploy_wait_available("aiocluster-test", "test-deploy")

    pods = await kubernetes.list_deploy_pods("aiocluster-test", "test-deploy")
    assert len(pods) > 0

    time.sleep(2)

    log = await kubernetes.get_execution_log("aiocluster-test", "test-deploy", pods[0].id)
    assert "ready for start up" in log

    result = await kubernetes.get_scale_deploy("aiocluster-test", "test-deploy")
    assert result == 1

    result = await kubernetes.set_scale_deploy("aiocluster-test", "test-deploy", 3)
    assert result['spec']['replicas'] == 3

    deploy_info = await kubernetes.get_deploy("aiocluster-test", "test-deploy")
    assert deploy_info._raw['spec']['replicas'] == 3

    ports = [{
        "name": "http-port",
        "port": 80,
        "protocol": "TCP",
        "targetPort": 80
    }]
    selector = {
        "app": "nginx"
    }
    service = await kubernetes.caller.create_service("aiocluster-test", "test-deploy", ports=ports, selector=selector, type="ClusterIP")
    assert service['spec'].get('clusterIP') is not None

    service = await kubernetes.caller.get_service("aiocluster-test", "test-deploy")
    assert service._raw['spec'].get('clusterIP') is not None

    service = await kubernetes.caller.delete_service("aiocluster-test", "test-deploy", True)
    assert service is True

    result = await kubernetes.delete_deploy("aiocluster-test", "test-deploy", True, timeout=120)
    assert result is True

    job_info = await kubernetes.get_deploy("aiocluster-test", "test-deploy")
    assert job_info is None


async def test_get_statefulset_k8s(kubernetes):
    # We clean up all the jobs on the namespace

    result = await kubernetes.get_nodes()
    assert len(result) > 0

    jobs_info = await kubernetes.list_statefulsets("aiocluster-test")
    assert jobs_info.total == 0

    await kubernetes.create_statefulset(
        "aiocluster-test",  # namespace
        "test-statefulset",  # jobid
        "nginx",  # image
        {
            "app": "nginx"
        },
        serviceName="aiocluster-test"
    )

    statefulset_info = await kubernetes.get_statefulset("aiocluster-test", "test-statefulset")
    assert statefulset_info.id == "test-statefulset"

    statefulsets_info = await kubernetes.list_statefulsets("aiocluster-test")
    assert statefulsets_info.total == 1

    # CONDITIONS not working in current version of statefulset api
    # Meanwhile we need to wait some time so the rest of tests can pass
    # await kubernetes.statefulset_wait_available("aiocluster-test", "test-statefulset")

    time.sleep(5)

    pods = await kubernetes.list_statefulset_pods("aiocluster-test", "test-statefulset")
    assert len(pods) > 0

    log = await kubernetes.get_execution_log("aiocluster-test", "test-statefulset", pods[0].id)
    assert "ready for start up" in log

    result = await kubernetes.get_scale_statefulset("aiocluster-test", "test-statefulset")
    assert result == 1

    result = await kubernetes.set_scale_statefulset("aiocluster-test", "test-statefulset", 3)
    assert result['spec']['replicas'] == 3

    statefulset_info = await kubernetes.get_statefulset("aiocluster-test", "test-statefulset")
    assert statefulset_info._raw['spec']['replicas'] == 3

    ports = [{
        "name": "http-port",
        "port": 80,
        "protocol": "TCP",
        "targetPort": 80
    }]
    selector = {
        "app": "nginx"
    }
    service = await kubernetes.caller.create_service("aiocluster-test", "test-statefulset", ports=ports, selector=selector, type="ClusterIP")
    assert service['spec'].get('clusterIP') is not None

    service = await kubernetes.caller.get_service("aiocluster-test", "test-statefulset")
    assert service._raw['spec'].get('clusterIP') is not None

    service = await kubernetes.caller.delete_service("aiocluster-test", "test-statefulset", True)
    assert service is True

    result = await kubernetes.delete_statefulset("aiocluster-test", "test-statefulset", True, timeout=120)
    assert result is True

    job_info = await kubernetes.get_statefulset("aiocluster-test", "test-statefulset")
    assert job_info is None
async def test_get_jobs_k8s(kubernetes):
    # We clean up all the jobs on the namespace

    result = await kubernetes.get_nodes()
    assert len(result) > 0

    result = await kubernetes.cleanup_jobs("aiocluster-test")
    assert result == 0

    jobs_info = await kubernetes.list_jobs("aiocluster-test")
    assert jobs_info.total == 0

    await kubernetes.create_job(
        "aiocluster-test",  # namespace
        "test-job",  # jobid
        "perl",  # image
        command=["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"],
    )

    job_info = await kubernetes.get_job("aiocluster-test", "test-job")
    assert job_info.id == "test-job"

    jobs_info = await kubernetes.list_jobs("aiocluster-test")
    assert jobs_info.total == 1

    result = await kubernetes.wait_for_job("aiocluster-test", "test-job")
    assert result == 1

    job_info = await kubernetes.get_job("aiocluster-test", "test-job")
    assert job_info.finished
    assert job_info.id == "test-job"

    executions = await kubernetes.list_job_executions("aiocluster-test", "test-job")
    assert len(executions) > 0

    log = await kubernetes.get_execution_log("aiocluster-test", "test-job", executions[0].internal_id)
    assert "3.14" in log

    result = await kubernetes.delete_job("aiocluster-test", "test-job")
    assert result is True

    job_info = await kubernetes.get_job("aiocluster-test", "test-job")
    assert job_info is None


async def test_get_jobs_limit_k8s(kubernetes):
    # We clean up all the jobs on the namespace

    result = await kubernetes.define_quota("aiocluster-test", cpu_limit="400m", mem_limit="900M")
    assert result is True

    result = await kubernetes.create_job(
        "aiocluster-test",  # namespace
        "test-job",  # jobid
        "tensorflow/tensorflow:1.13.2-py3-jupyter",  # image
        cpu_limit="300m",
        mem_limit="800M",
        command=["jupyter-nbconvert"],
        args=[
            "--execute",
            "/tf/tensorflow-tutorials/basic_classification.ipynb",
            "--ExecutePreprocessor.timeout=380",
        ],
    )
    assert result is True

    await asyncio.sleep(5)

    result = await kubernetes.create_job(
        "aiocluster-test",  # namespace
        "test-job-2",  # jobid
        "tensorflow/tensorflow:1.13.2-py3-jupyter",  # image
        cpu_limit="300m",
        mem_limit="800M",
        command=["jupyter-nbconvert"],
        args=[
            "--execute",
            "/tf/tensorflow-tutorials/basic_classification.ipynb",
            "--ExecutePreprocessor.timeout=380",
        ],
    )
    assert result is True

    await asyncio.sleep(20)

    # we want to wait that the first job starts

    result = await kubernetes.wait_for_job_execution_status("aiocluster-test", "test-job")
    assert result == "Running"

    result = await kubernetes.waiting_jobs("aiocluster-test")
    assert len(result) == 1
    assert result[0] == "test-job-2"

    result = await kubernetes.running_jobs("aiocluster-test")
    assert len(result) == 1
    assert result[0] == "test-job"

    result = await kubernetes.delete_job("aiocluster-test", "test-job")
    assert result is True

    await asyncio.sleep(50)

    result = await kubernetes.waiting_jobs("aiocluster-test")
    assert len(result) >= 0

    result = await kubernetes.running_jobs("aiocluster-test")
    assert len(result) <= 1


# async def test_get_tfjobs_k8s(kubernetes):
#     # We clean up all the jobs on the namespace

#     result = await kubernetes.define_quota("aiocluster-test", cpu_limit="400m", mem_limit="900M")
#     assert result is True

#     await kubernetes.install_tfjobs("aiocluster-test")

#     result = await kubernetes.create_tfjob(
#         "aiocluster-test",  # namespace
#         "test-tfjob",  # jobid
#         "gcr.io/tf-on-k8s-dogfood/tf_sample:dc944ff",  # image
#         cpu_limit="300m",
#         mem_limit="800M",
#         workers=1,
#         ps=2,
#         masters=1,
#     )
#     assert result is True

#     await kubernetes.get_tfjob("aiocluster-test", "test-tfjob")

#     await kubernetes.list_tfjobs("aiocluster-test")
