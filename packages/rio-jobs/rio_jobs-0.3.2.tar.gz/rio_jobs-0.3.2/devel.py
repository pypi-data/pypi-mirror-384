import asyncio
from datetime import timedelta, datetime, timezone
import rio
import typing as t
import functools
import rio_jobs
import random

import rio_jobs.components


class MyRoot(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio_jobs.components.JobsView(scheduler),
            rio_jobs.components.RunsView(scheduler),
            spacing=2,
            min_width=50,
            align_x=0.5,
            align_y=0.5,
        )


# Create a scheduler
scheduler = rio_jobs.JobScheduler(
    keep_past_runs_for=timedelta(seconds=10),
    keep_past_n_runs=5,
)


# Create a function for the scheduler to run. This function can by synchronous
# or asynchronous. The `@scheduler.job` decorator adds the function to the
# scheduler.
@scheduler.job(
    timedelta(seconds=2),
    soft_start=False,
    wait_for_initial_interval=False,
)
async def my_job(run: rio_jobs.Run) -> t.Any:
    print(f"I got the app! {run.app}, {run.app is app}")

    for ii in range(10):
        if random.random() < 0.05:
            raise ValueError("Random failure")

        await asyncio.sleep(1)
        run.progress = ii / 9

    if random.random() < 0.1:
        return "never"


# Pass the scheduler to the Rio app. Since Rio's extension interface isn't
# stable yet, we'll add the extension manually after the app has been created.
app = rio.App(
    build=MyRoot,
)

app._add_extension(scheduler)
