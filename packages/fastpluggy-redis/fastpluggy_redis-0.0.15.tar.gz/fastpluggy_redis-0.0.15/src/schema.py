from typing import Optional, Any, List

from pydantic import BaseModel, Field


class RedisKey(BaseModel):
    key: str
    type: str
    ttl: int
    size: Optional[int] = None
    preview: Optional[Any] = None
    value: Any = None



class RedisInfo(BaseModel):
    # --- Server / General ---
    redis_version: Optional[str] = Field(
        None, description="Redis server version (e.g. '7.2.5')"
    )
    redis_mode: Optional[str] = Field(
        None, description="Redis mode ('standalone', 'sentinel', or 'cluster')"
    )
    os: Optional[str] = Field(
        None, description="Operating system and kernel (e.g. 'Linux 6.12.5-linuxkit x86_64')"
    )
    uptime_in_seconds: Optional[int] = Field(
        None, description="Number of seconds the server has been running"
    )
    uptime_in_days: Optional[int] = Field(
        None, description="Number of days the server has been running"
    )
    process_id: Optional[int] = Field(
        None, description="OS process ID of the Redis server"
    )
    tcp_port: Optional[int] = Field(
        None, description="TCP port Redis is listening on (e.g. 6379)"
    )

    # --- Clients ---
    connected_clients: Optional[int] = Field(
        None, description="Number of client connections (excluding replicas)"
    )
    blocked_clients: Optional[int] = Field(
        None, description="Number of clients blocked in blocking commands"
    )
    clients_in_timeout_table: Optional[int] = Field(
        None, description="Number of clients in the timeout table"
    )
    rejected_connections: Optional[int] = Field(
        None, description="Total connections rejected because maxclients was reached"
    )
    maxclients: Optional[int] = Field(
        None, description="Configured maximum number of client connections"
    )

    # --- Memory (raw integers + human strings) ---
    used_memory: Optional[int] = Field(
        None, description="Total memory used by Redis in bytes"
    )
    used_memory_human: Optional[str] = Field(
        None, description="Total memory used by Redis (human-readable, e.g. '966.82K')"
    )
    used_memory_rss: Optional[int] = Field(
        None, description="RSS memory used by Redis in bytes"
    )
    used_memory_rss_human: Optional[str] = Field(
        None, description="RSS memory (human-readable, e.g. '14.80M')"
    )
    mem_fragmentation_ratio: Optional[float] = Field(
        None, description="Memory fragmentation ratio (RSS / used_memory)"
    )
    maxmemory: Optional[int] = Field(
        None, description="Configured maxmemory in bytes (0 if none set)"
    )
    maxmemory_human: Optional[str] = Field(
        None, description="Configured maxmemory (human-readable, e.g. '0B')"
    )
    total_system_memory: Optional[int] = Field(
        None, description="Total system RAM in bytes"
    )
    total_system_memory_human: Optional[str] = Field(
        None, description="Total system RAM (human-readable, e.g. '7.75G')"
    )

    # --- Stats (Commands / Network) ---
    total_commands_processed: Optional[int] = Field(
        None, description="Cumulative number of commands processed since startup"
    )
    total_connections_received: Optional[int] = Field(
        None, description="Total number of connections accepted since startup"
    )
    instantaneous_ops_per_sec: Optional[int] = Field(
        None, description="Operations per second over the last second"
    )
    total_net_input_bytes: Optional[int] = Field(
        None, description="Total number of bytes read from the network"
    )
    total_net_output_bytes: Optional[int] = Field(
        None, description="Total number of bytes written to the network"
    )
    instantaneous_input_kbps: Optional[float] = Field(
        None, description="Current network input rate in KB/sec"
    )
    instantaneous_output_kbps: Optional[float] = Field(
        None, description="Current network output rate in KB/sec"
    )
    expired_keys: Optional[int] = Field(
        None, description="Total keys expired since startup"
    )
    evicted_keys: Optional[int] = Field(
        None, description="Total keys evicted due to maxmemory policy"
    )
    keyspace_hits: Optional[int] = Field(
        None, description="Number of successful key lookups"
    )
    keyspace_misses: Optional[int] = Field(
        None, description="Number of failed key lookups"
    )

    # --- Persistence (RDB / AOF) ---
    aof_enabled: Optional[int] = Field(
        None, description="1 if AOF is enabled, 0 otherwise"
    )
    rdb_bgsave_in_progress: Optional[int] = Field(
        None, description="1 if a background RDB save is in progress, 0 otherwise"
    )
    rdb_last_bgsave_time_sec: Optional[int] = Field(
        None, description="Seconds taken by the last RDB background save (-1 if never run)"
    )
    aof_current_rewrite_time_sec: Optional[int] = Field(
        None, description="Seconds taken by the last AOF rewrite (-1 if none yet)"
    )

    # --- Replication ---
    role: Optional[str] = Field(
        None, description="Server role: 'master' or 'replica'"
    )
    connected_slaves: Optional[int] = Field(
        None, description="Number of replicas currently connected"
    )
    master_repl_offset: Optional[int] = Field(
        None, description="Replication offset of the master"
    )
    repl_backlog_active: Optional[int] = Field(
        None, description="1 if replication backlog is active, 0 otherwise"
    )

    # --- CPU Usage (raw floats) ---
    used_cpu_sys: Optional[float] = Field(
        None, description="System CPU time consumed by Redis (seconds)"
    )
    used_cpu_user: Optional[float] = Field(
        None, description="User CPU time consumed by Redis (seconds)"
    )
    used_cpu_sys_children: Optional[float] = Field(
        None, description="System CPU time used by background children processes (seconds)"
    )
    used_cpu_user_children: Optional[float] = Field(
        None, description="User CPU time used by background children processes (seconds)"
    )

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    @property
    def uptime_text(self) -> str:
        """
        Convert `uptime_in_seconds` into an “Xh Ym” string.
        If `uptime_in_seconds` is None, returns '0h 0m'.
        """
        seconds = self.uptime_in_seconds or 0
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    @property
    def cpu_load(self) -> float:
        """
        Sum of `used_cpu_user` and `used_cpu_sys`. If either is None, treat as 0.0.
        """
        user = self.used_cpu_user or 0.0
        sys_ = self.used_cpu_sys or 0.0
        return user + sys_

    @property
    def hits_misses(self) -> str:
        """
        Returns a “hits/misses” string, e.g. '123 / 45'. If either is None, treat as 0.
        """
        hits = self.keyspace_hits or 0
        misses = self.keyspace_misses or 0
        return f"{hits}/{misses}"

    class Config:
        json_schema_extra = {
            "example": {
                "redis_version": "7.2.5",
                "redis_mode": "standalone",
                "os": "Linux 6.12.5-linuxkit x86_64",
                "uptime_in_seconds": 3600,
                "uptime_in_days": 0,
                "process_id": 1,
                "tcp_port": 6379,
                "connected_clients": 1,
                "blocked_clients": 0,
                "clients_in_timeout_table": 0,
                "rejected_connections": 0,
                "maxclients": 10000,
                "used_memory": 990024,
                "used_memory_human": "966.82K",
                "used_memory_rss": 15519744,
                "used_memory_rss_human": "14.80M",
                "mem_fragmentation_ratio": 15.71,
                "maxmemory": 0,
                "maxmemory_human": "0B",
                "total_system_memory": 8324849664,
                "total_system_memory_human": "7.75G",
                "total_commands_processed": 17,
                "total_connections_received": 5,
                "instantaneous_ops_per_sec": 1,
                "total_net_input_bytes": 683,
                "total_net_output_bytes": 5353,
                "instantaneous_input_kbps": 0.07,
                "instantaneous_output_kbps": 0.01,
                "expired_keys": 0,
                "evicted_keys": 0,
                "keyspace_hits": 0,
                "keyspace_misses": 0,
                "aof_enabled": 0,
                "rdb_bgsave_in_progress": 0,
                "rdb_last_bgsave_time_sec": -1,
                "aof_current_rewrite_time_sec": -1,
                "role": "master",
                "connected_slaves": 0,
                "master_repl_offset": 0,
                "repl_backlog_active": 0,
                "used_cpu_sys": 0.118575,
                "used_cpu_user": 0.065875,
                "used_cpu_sys_children": 0.00798,
                "used_cpu_user_children": 0.002734,
            }
        }

class SlowLogEntry(BaseModel):
    id: Optional[int] = Field(
        None, description="Unique slowlog entry ID"
    )
    start_time: Optional[int] = Field(
        None, description="Unix timestamp when the slowlog entry was created"
    )
    duration: Optional[int] = Field(
        None, description="Execution time in microseconds"
    )
    command: Optional[bytes| str] = Field(
        None, description="The raw command (as bytes or str) that triggered the slowlog entry"
    )
    client_address: Optional[bytes| str] = Field(
        None, description="Client IP:port (bytes or str) that issued the slow command"
    )
    client_name: Optional[bytes| str] = Field(
        None, description="Client name (if any) that issued the slow command"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 142013,
                "start_time": 1749026813,
                "duration": 16464,
                "command": b"CLIENT SETINFO LIB-NAME redis-py",
                "client_address": b"fd40:e282:111:f505:6e11:200:a23:e2d:37362",
                "client_name": b""
            }
        }

class RedisCommandRequest(BaseModel):
    command: str = Field(..., description="The Redis command to execute")
    db: Optional[int] = Field(None, description="Database index to use")

    class Config:
        json_schema_extra = {
            "example": {
                "command": "GET mykey",
                "db": 0
            }
        }

class RedisCommandResponse(BaseModel):
    command: str = Field(..., description="The Redis command that was executed")
    result: Any = Field(None, description="The result of the command execution")
    error: Optional[str] = Field(None, description="Error message if the command failed")

    class Config:
        json_schema_extra = {
            "example": {
                "command": "GET mykey",
                "result": "value",
                "error": None
            }
        }
