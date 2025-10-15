import pytest

from birdbrain_tasks import BirdbrainTasks

async def method_1(p):
    for i in range(40):
        print("method_1 running", p, i)

        await BirdbrainTasks.yield_task()

    return("method_1_return")

async def method_2(p):
    for i in range(20):
        print("method_2 running", p, i)

        await BirdbrainTasks.yield_task()

    return(2)

async def method_3():
    for i in range(30):
        print("method_3 running", i)

        await BirdbrainTasks.yield_task()

def test_tasks_with_wait():
    tasks = BirdbrainTasks()

    tasks.create_task(method_1(999))
    tasks.create_task(method_2("text"))
    tasks.create_task(method_3())

    tasks.run()

    assert tasks.result("method_1") == "method_1_return"
    assert tasks.result("method_2") == 2
    assert tasks.result("method_3") is None
    assert tasks.result("unknown") is None
    assert tasks.result(None) is None
