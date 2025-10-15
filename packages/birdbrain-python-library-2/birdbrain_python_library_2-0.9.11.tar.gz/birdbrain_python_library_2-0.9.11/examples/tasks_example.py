from birdbrain_hummingbird import BirdbrainHummingbird
from birdbrain_tasks import BirdbrainTasks

import asyncio
import random

async def random_blinker(hummingbird):
    for i in range(35):
        hummingbird.tri_led(1, random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))

        await BirdbrainTasks.yield_task()

    return("random_blinker")  # return is optional

async def blue_blinker(hummingbird):
    for i in range(35):
        hummingbird.tri_led(1, 0, 0, 100)

        await BirdbrainTasks.yield_task()


hummingbird = BirdbrainHummingbird('A')

tasks = BirdbrainTasks()

tasks.create_task(random_blinker(hummingbird))
tasks.create_task(blue_blinker(hummingbird))

tasks.run()

random_blinker_result = tasks.result("random_blinker")

hummingbird.tri_led(1, 0, 0, 0)
