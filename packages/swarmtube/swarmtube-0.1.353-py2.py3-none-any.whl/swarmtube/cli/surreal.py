# import asyncio
# import random
import time
import click

from agptools.helpers import parse_uri
from agptools.logs import logger

# from bigplanner.helpers import *
from swarmtube.cli.main import main, CONTEXT_SETTINGS
from swarmtube.cli.config import config

# from bigplanner.definitions import DEFAULT_LANGUAGE, UID_TYPE

# TODO: include any logic from module core
# Examples
# from bigplanner.models import *
# from bigplanner.logic import Tagger
# from syncmodels.storage import Storage

# Import local inventory models
# from bigplanner.models.task import PlannerTask as Item
# from bigplanner.models.task import PlannerTaskRequest as Request
# from bigplanner.models.task import PlannerTaskResponse as Response

from syncmodels.helpers.surreal import SurrealServer
from syncmodels.helpers.faker import fake

from surrealist import Surreal


from ..definitions import MONOTONIC_KEY

# ---------------------------------------------------------
# Dynamic Loading Interface / EP Exposure
# ---------------------------------------------------------
TAG = "SURREAL"
DESCRIPTION = "SurrealDB CLI API"
API_ORDER = 10

# ---------------------------------------------------------
# Loggers
# ---------------------------------------------------------

log = logger(__name__)


# ---------------------------------------------------------
# Task CLI port implementation
# ---------------------------------------------------------
@main.group(context_settings=CONTEXT_SETTINGS)
@click.pass_obj
def surreal(env):
    """subcommands for manage tasks for bigplanner"""
    # banner("User", env.__dict__)


submodule = surreal


@submodule.command()
@click.option("--path", default=None)
@click.pass_obj
def start(env, path):
    """Start Surreal Server"""
    # force config loading
    config.callback()

    db_path = env.db_url
    surreal_url = env.surreal_url
    uri = parse_uri(surreal_url)
    bind = "0.0.0.0:{port}".format_map(uri)
    server = SurrealServer(path=db_path, bind=bind, daemon=True)
    if server.start():
        log.info("Surreal Server running: %s : %s", bind, db_path)
        log.info("User `swarmtube surreal stop` for stopping server")
    else:
        log.error("Launching Surreal server FAILED: %s : %s", bind, db_path)


@submodule.command()
@click.pass_obj
def stop(env):
    """Stop Surreal Server"""
    # force config loading
    config.callback()

    db_path = env.db_url
    surreal_url = env.surreal_url
    uri = parse_uri(surreal_url)
    bind = "0.0.0.0:{port}".format_map(uri)
    server = SurrealServer(path=db_path, bind=bind, daemon=True)
    if server.stop():
        log.info("Surreal Server stopped: %s : %s", bind, db_path)
    else:
        log.info("Unable to Stop Server: %s : %s", bind, db_path)


@submodule.command()
@click.option("--rate", default=2.0)
@click.option("--events", default=10000)
@click.pass_obj
def publish(env, rate, events):
    """Example of publishing something to SurrealDB"""
    # force config loading
    config.callback()

    db_path = env.db_url
    server = SurrealServer(path=db_path, daemon=True)

    url = f"http://localhost:{server.bind.split(':')[-1]}"

    db = Surreal(
        # "http://localhost:9000",
        url,
        namespace="test",
        database="test",
        credentials=("root", "root"),
        use_http=False,
        timeout=10,
        log_level="ERROR",
    )
    print(db.is_ready())  # prints True if server up and running on that url
    print(db.version())  # prints server version

    with db.connect() as db:
        t0 = time.time()
        t2 = 0
        i = 0
        name = fake.name()
        surname = fake.name()
        while events != 0:

            phone = fake.phone_number()
            surname = fake.name()
            name = fake.name()

            data = {
                "name": f"{name}-{i}",
                "surname": f"{surname}-{i}",
                "phone": phone,
            }
            db.create("person", data)
            events -= 1
            i += 1

            if t2 < (t1 := time.time()):
                query = """
                SELECT COUNT() FROM person GROUP ALL;
                """
                res = db.query(query)
                log.info("%s", res.result)
                # res = db.select("person")
                # elapsed = time.time() - t1
                # log.info(f"elapsed: {elapsed} / {len(res.result)}")

                t2 = t1 + 2
                log.info("+ [%s] %s", i, data)
                speed = i / (t1 - t0)
                log.info("speed: %s rows / sec", speed)

            if rate > 0:
                time.sleep(rate)

        speed = events / (t1 - t0)
        log.info("> Speed: %s rows / sec", speed)


@submodule.command()
@click.option("--events", default=1000)
@click.pass_obj
def subscribe(env, events):
    """Example of subscribing to something from SurrealDB"""
    # force config loading
    config.callback()

    db_path = env.db_url
    server = SurrealServer(path=db_path, daemon=True)

    url = f"http://localhost:{server.bind.split(':')[-1]}"

    db = Surreal(
        # "http://localhost:9000",
        url,
        namespace="test",
        database="test",
        credentials=("root", "root"),
        use_http=False,
        timeout=10,
        log_level="ERROR",
    )
    print(db.is_ready())  # prints True if server up and running on that url
    print(db.version())  # prints server version

    received = 0

    def call_back(response: dict) -> None:
        nonlocal received
        received += 1
        print(f"[{received}] : {response}")

    with db.connect() as db:
        log.info("Creating LQ")
        res = db.live("person", callback=call_back)

        log.info("Listening events ...")
        while received < events:
            time.sleep(0.5)

        log.info("Stop LQ")
        live_id = res.result  # live_id is a LQ id, we need it to kill a query
        db.kill(live_id)  # we kill LQ, no more events to come


# ----------------------------------------------------------
# TODO: delete from this point
# ----------------------------------------------------------


@submodule.command()
# @click.option("--events", default=1000)
@click.pass_obj
def count(env):
    """Find and list existing tasks for bigplanner"""
    # force config loading
    config.callback()

    db_path = env.db_url
    server = SurrealServer(path=db_path, daemon=True)

    url = f"http://localhost:{server.bind.split(':')[-1]}"

    surreal = Surreal(
        # "http://localhost:9000",
        url,
        namespace="test",
        database="test",
        credentials=("root", "root"),
        use_http=False,
        timeout=10,
        log_level="ERROR",
    )
    print(surreal.is_ready())  # prints True if server up and running on that url
    print(surreal.version())  # prints server version

    with surreal.connect() as db:
        log.info(f"Selecting LQ")
        query = """
        SELECT COUNT() FROM person GROUP ALL;
        """
        res = db.query(query)
        log.info(f"{res.result}")


@submodule.command()
# @click.option("--events", default=1000)
@click.option("--cycles", default=-1)
@click.pass_obj
def swarmflow1(env, cycles):
    """Find and list existing tasks for bigplanner"""
    # force config loading
    config.callback()

    async def main():

        db_path = env.db_url
        server = SurrealServer(path=db_path, daemon=True)
        url = f"http://localhost:{server.bind.split(':')[-1]}"

        from ..logic.swarmflow import SurrealBroker, SurrealStorage, PlusOne

        broker = SurrealBroker(url)
        storage = SurrealStorage(url)

        uid = "random_plus_one"
        sources = ["clock"]

        particle = PlusOne(uid, sources, broker, storage)
        await particle.run()

    asyncio.run(main())


@submodule.command()
@click.option("--rate", default=2.0)
@click.option("--events", default=-1)
@click.option("--cycles", default=-1)
@click.pass_obj
def clock(env, rate, events, cycles):
    """Find and list existing tasks for bigplanner"""
    config.callback()

    db_path = env.db_url
    server = SurrealServer(path=db_path, daemon=True)

    url = f"http://localhost:{server.bind.split(':')[-1]}"

    surreal = Surreal(
        # "http://localhost:9000",
        url,
        namespace="test",
        database="test",
        credentials=("root", "root"),
        use_http=False,
        timeout=10,
        log_level="ERROR",
    )
    print(surreal.is_ready())  # prints True if server up and running on that url
    print(surreal.version())  # prints server version

    uid = "clock"
    with surreal.connect() as conn:
        while events != 0:
            t0 = time.time()
            data = {
                MONOTONIC_KEY: t0,
                #'uid': uid,
                "payload": events,
            }
            conn.create(uid, data)
            log.info(f"{data}")
            time.sleep(rate)
            events -= 1


@submodule.command()
@click.option("--rate", default=2.0)
@click.option("--events", default=10)
@click.option("--cycles", default=-1)
@click.pass_obj
def temperatures(env, rate, events, cycles):
    """Find and list existing tasks for bigplanner"""
    config.callback()

    db_path = env.db_url
    server = SurrealServer(path=db_path, daemon=True)

    url = f"http://localhost:{server.bind.split(':')[-1]}"

    surreal = Surreal(
        # "http://localhost:9000",
        url,
        namespace="test",
        database="test",
        credentials=("root", "root"),
        use_http=False,
        timeout=10,
        log_level="ERROR",
    )

    uids = "temp_in", "temp_out"
    temp0 = [22, 15]
    inertia = [1, 10]
    temps = [
        [21.0, 17.5],  # t
        [0.1, 0.3],  # t'
        [0, 0],  # t''
    ]

    def step():
        s = 0.1
        for i, zero in enumerate(temp0):
            d = zero - temps[0][i]
            a = d / inertia[i]
            temps[2][i] = a
            temps[1][i] += a * s
            temps[0][i] += temps[1][i] * s

    conn = surreal.connect()

    def publish(idx: int):
        uid = uids[idx]
        t0 = time.time()
        data = {
            MONOTONIC_KEY: t0,
            "payload": temps[0][idx],
        }
        conn.create(uid, data)
        log.info(f"+ [{idx}]: {data}")

    counter = list(inertia)
    while events > 0:
        time.sleep(rate)
        step()
        for i, value in enumerate(counter):
            value -= 1
            if value <= 0 and random.random() < 0.25:
                value = inertia[i]
                publish(i)
                events -= 1
            counter[i] = value


@submodule.command()
# @click.option("--events", default=1000)
@click.option("--cycles", default=-1)
@click.pass_obj
def swarmflow2(env, cycles):
    """Find and list existing tasks for bigplanner"""
    # force config loading
    config.callback()

    async def main():

        db_path = env.db_url
        server = SurrealServer(path=db_path, daemon=True)
        url = f"http://localhost:{server.bind.split(':')[-1]}"

        from ..logic.swarmflow import SurrealBroker, SurrealStorage, TempDiff

        broker = SurrealBroker(url)
        storage = SurrealStorage(url)

        uid = "temp_diff"
        sources = "temp_in", "temp_out"

        particle = TempDiff(uid, sources, broker, storage)
        await particle.run()

    asyncio.run(main())
