import os

import pytest
import redis
from fastpluggy.core.database import create_table_if_not_exist
from fastpluggy.core.models import AppSettings
from testcontainers.redis import RedisContainer

from src.redis_connector import RedisConnection


@pytest.fixture(scope="session")
def redis_container():
    create_table_if_not_exist(AppSettings)
    container = RedisContainer("redis:7.2")
    container.start()
    yield container
    container.stop()


@pytest.fixture()
def connection(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    print(f"Connecting to Redis at {host}:{port}")
    os.environ["redis_host"] = host
    os.environ["redis_port"] = str(port)
    conn = RedisConnection()

    # Setup data in multiple databases
    for db in range(2):
        r = redis.Redis(host=host, port=int(port), db=db, decode_responses=True)
        r.set(f"key_str_{db}", f"value{db}")
        r.hset(f"key_hash_{db}", mapping={"a": "1", "b": "2"})
        r.lpush(f"key_list_{db}", "item1", "item2")
        r.sadd(f"key_set_{db}", "one", "two")
    return conn


def test_connection_success(connection):
    assert connection.test_connection() is True


def test_get_key_info_string(connection):
    info = connection.get_key_details("key_str_0", preview_mode=True)
    assert info.key == "key_str_0"
    assert info.type == "string"
    assert info.preview.startswith("b'value")


def test_get_key_info_list(connection):
    info = connection.get_key_details("key_list_0", preview_mode=True)
    assert info.type == "list"
    assert "item" in info.preview


def test_get_key_info_hash(connection):
    info = connection.get_key_details("key_hash_0", preview_mode=True)
    assert info.type == "hash"
    assert "a" in info.preview


def test_get_key_info_set(connection):
    info = connection.get_key_details("key_set_0", preview_mode=True)
    assert info.type == "set"
    assert "one" in info.preview or "two" in info.preview


def test_get_keys(connection):
    keys = connection.get_keys("*_0")
    assert all(k.key.endswith("_0") for k in keys)
    assert len(keys) == 4


def test_get_key_data(connection):
    data = connection.get_key_details("key_hash_0")
    assert data.type == "hash"
    assert b'a' in data.value


def test_select_db(connection):
    assert connection.select_db(1) is True
    assert connection.get_current_db() == 1
    data = connection.get_key_details("key_str_1")
    assert data.value == "b'value1'"


def test_get_databases(connection):
    dbs = connection.get_databases()
    print(f"DBs: {dbs}")
    assert isinstance(dbs, list)
    assert any(db["current"] is True for db in dbs)


def test_delete_key(connection):
    assert connection.delete_key("key_str_0") is True
    assert connection.get_key_details("key_str_0").value is None


def test_flush_db(connection):
    connection.flush_db()
    keys = connection.get_keys()
    assert len(keys) == 0
