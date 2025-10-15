import asyncio

class BirdbrainTasks:
    def __init__(self):
        self.method_list = []
        self.task_list = []
        self.results = {}
        
    def result(self, method_name):
        return self.results[method_name] if method_name in self.results else None

    def create_task(self, method):
        self.method_list.append(method)

    def run(self):
        asyncio.run(self.runner())

    async def wait(self):
        while True:
            running_task_count = 0

            for task in self.task_list:
                try:
                    self.results[task.get_coro().__name__] = task.result()
                except asyncio.exceptions.InvalidStateError:
                    pass

                if not task.done(): running_task_count += 1

            if running_task_count == 0: break

            await self.yield_task()

    async def runner(self):
        for method_name in self.method_list:
            self.task_list.append(asyncio.create_task(method_name))

        await self.wait()

    @classmethod
    async def yield_task(self, yield_time = 0.0):
        await asyncio.sleep(yield_time)
