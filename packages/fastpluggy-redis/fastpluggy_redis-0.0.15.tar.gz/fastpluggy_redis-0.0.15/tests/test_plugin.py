import pytest
import redis
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def redis_container():
    container = RedisContainer("redis:7.2")
    container.start()
    yield container
    container.stop()

@pytest.fixture()
def redis_client(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    client = redis.Redis(host=host, port=int(port), db=0)

    # Init sample data in multiple databases
    for db in range(3):
        r = redis.Redis(host=host, port=int(port), db=db)
        r.set("key_string", f"value_db{db}")
        r.hset("key_hash", mapping={"field1": f"val{db}", "field2": f"val{db+1}"})
        r.lpush("key_list", f"item{db}", f"item{db+1}")
        r.sadd("key_set", f"member{db}", f"member{db+1}")

    return client

def test_string_key(redis_client):
    assert redis_client.get("key_string").startswith(b"value_")

def test_hash_key(redis_client):
    assert redis_client.hgetall("key_hash")

def test_list_key(redis_client):
    assert redis_client.llen("key_list") > 0

def test_set_key(redis_client):
    assert redis_client.scard("key_set") > 0
