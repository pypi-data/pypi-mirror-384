#!/usr/bin/env python3
"""
Redis gRPC Client
Redis cache client
"""

from typing import List, Dict, Optional
from .base_client import BaseGRPCClient
from .proto import redis_service_pb2, redis_service_pb2_grpc


class RedisClient(BaseGRPCClient):
    """Redis gRPC Client"""

    def __init__(self, host: str = 'localhost', port: int = 50055, user_id: Optional[str] = None,
                 organization_id: Optional[str] = None, lazy_connect: bool = True,
                 enable_compression: bool = True, enable_retry: bool = True):
        """
        Initialize Redis client

        Args:
            host: Service host (default: localhost)
            port: Service port (default: 50055)
            user_id: User ID
            organization_id: Organization ID
            lazy_connect: Lazy connection (default: True)
            enable_compression: Enable compression (default: True)
            enable_retry: Enable retry (default: True)
        """
        super().__init__(host, port, user_id, lazy_connect, enable_compression, enable_retry)
        self.organization_id = organization_id or 'default-org'

    def _create_stub(self):
        """Create Redis service stub"""
        return redis_service_pb2_grpc.RedisServiceStub(self.channel)

    def service_name(self) -> str:
        return "Redis"

    def health_check(self) -> Optional[Dict]:
        """Health check"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.HealthCheckRequest(
                user_id=self.user_id
            )
            response = self.stub.HealthCheck(request)

            print(f"✅ [Redis] Service status: {response.status}")
            print(f"   Healthy: {response.healthy}")
            print(f"   Redis version: {response.redis_version}")
            print(f"   Connected clients: {response.connected_clients}")

            return {
                'status': response.status,
                'healthy': response.healthy,
                'redis_version': response.redis_version,
                'connected_clients': response.connected_clients,
                'uptime_seconds': response.uptime_seconds
            }

        except Exception as e:
            return self.handle_error(e, "Health check")

    def set(self, key: str, value: str, ttl_seconds: int = 0) -> Optional[bool]:
        """Set key-value"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.SetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                value=value,
                ttl_seconds=ttl_seconds
            )

            response = self.stub.Set(request)

            if response.success:
                print(f"✅ [Redis] Set successful: {key}")
                return True
            else:
                print(f"⚠️  [Redis] Set failed: {response.error}")
                return False

        except Exception as e:
            self.handle_error(e, "Set key-value")
            return False

    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.GetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.Get(request)

            if response.exists:
                print(f"✅ [Redis] Get successful: {key} = {response.value[:50]}...")
                return response.value
            else:
                print(f"⚠️  [Redis] Key not found: {key}")
                return None

        except Exception as e:
            return self.handle_error(e, "Get key-value")

    def delete(self, key: str) -> Optional[bool]:
        """Delete key"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.DeleteRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.Delete(request)

            if response.success:
                print(f"✅ [Redis] Delete successful: {key} (deleted {response.deleted_count} keys)")
                return True
            else:
                print(f"⚠️  [Redis] Delete failed: {response.error}")
                return False

        except Exception as e:
            self.handle_error(e, "Delete key")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.ExistsRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.Exists(request)

            print(f"✅ [Redis] Key '{key}' exists: {response.exists}")
            return response.exists

        except Exception as e:
            self.handle_error(e, "Check key exists")
            return False

    def set_with_ttl(self, key: str, value: str, ttl_seconds: int) -> Optional[bool]:
        """Set key-value with TTL"""
        return self.set(key, value, ttl_seconds)

    def mset(self, key_values: Dict[str, str]) -> Optional[bool]:
        """Batch set key-values"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.MSetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key_values=key_values
            )

            response = self.stub.MSet(request)

            if response.success:
                print(f"✅ [Redis] Batch set successful: {len(key_values)} keys")
                return True
            else:
                print(f"⚠️  [Redis] Batch set failed: {response.error}")
                return False

        except Exception as e:
            self.handle_error(e, "Batch set key-values")
            return False

    def mget(self, keys: List[str]) -> Dict[str, str]:
        """Batch get key-values"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.MGetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                keys=keys
            )

            response = self.stub.MGet(request)

            values = dict(response.values)
            print(f"✅ [Redis] Batch get successful: requested {len(keys)} keys, returned {len(values)} values")
            return values

        except Exception as e:
            return self.handle_error(e, "Batch get key-values") or {}

    def incr(self, key: str) -> Optional[int]:
        """Increment"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.IncrRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.Incr(request)

            if response.success:
                print(f"✅ [Redis] Increment successful: {key} = {response.value}")
                return response.value
            else:
                print(f"⚠️  [Redis] Increment failed: {response.error}")
                return None

        except Exception as e:
            return self.handle_error(e, "Increment")

    def decr(self, key: str) -> Optional[int]:
        """Decrement"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.DecrRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.Decr(request)

            if response.success:
                print(f"✅ [Redis] Decrement successful: {key} = {response.value}")
                return response.value
            else:
                print(f"⚠️  [Redis] Decrement failed: {response.error}")
                return None

        except Exception as e:
            return self.handle_error(e, "Decrement")

    def expire(self, key: str, seconds: int) -> Optional[bool]:
        """Set expiration time"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.ExpireRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                seconds=seconds
            )

            response = self.stub.Expire(request)

            if response.success:
                print(f"✅ [Redis] Expire set successful: {key} will expire in {seconds} seconds")
                return True
            else:
                print(f"⚠️  [Redis] Expire set failed: {response.error}")
                return False

        except Exception as e:
            self.handle_error(e, "Set expiration")
            return False

    def ttl(self, key: str) -> Optional[int]:
        """Get time to live (seconds)"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.TTLRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.TTL(request)

            if response.ttl >= 0:
                print(f"✅ [Redis] TTL: {key} has {response.ttl} seconds remaining")
            elif response.ttl == -1:
                print(f"✅ [Redis] TTL: {key} never expires")
            else:
                print(f"⚠️  [Redis] TTL: {key} does not exist")

            return response.ttl

        except Exception as e:
            return self.handle_error(e, "Get TTL")

    def lpush(self, key: str, values: List[str]) -> Optional[int]:
        """Left push to list"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.LPushRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                values=values
            )

            response = self.stub.LPush(request)

            if response.success:
                print(f"✅ [Redis] Left push successful: {key} length = {response.length}")
                return response.length
            else:
                print(f"⚠️  [Redis] Left push failed: {response.error}")
                return None

        except Exception as e:
            return self.handle_error(e, "Left push to list")

    def rpush(self, key: str, values: List[str]) -> Optional[int]:
        """Right push to list"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.RPushRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                values=values
            )

            response = self.stub.RPush(request)

            if response.success:
                print(f"✅ [Redis] Right push successful: {key} length = {response.length}")
                return response.length
            else:
                print(f"⚠️  [Redis] Right push failed: {response.error}")
                return None

        except Exception as e:
            return self.handle_error(e, "Right push to list")

    def lrange(self, key: str, start: int = 0, stop: int = -1) -> List[str]:
        """Get list range"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.LRangeRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                start=start,
                stop=stop
            )

            response = self.stub.LRange(request)

            if response.success:
                print(f"✅ [Redis] Get list successful: {key} returned {len(response.values)} elements")
                return list(response.values)
            else:
                print(f"⚠️  [Redis] Get list failed: {response.error}")
                return []

        except Exception as e:
            return self.handle_error(e, "Get list range") or []

    def hset(self, key: str, field: str, value: str) -> Optional[bool]:
        """Set hash field"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.HSetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                field=field,
                value=value
            )

            response = self.stub.HSet(request)

            if response.success:
                print(f"✅ [Redis] Hash set successful: {key}.{field}")
                return True
            else:
                print(f"⚠️  [Redis] Hash set failed: {response.error}")
                return False

        except Exception as e:
            self.handle_error(e, "Set hash field")
            return False

    def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.HGetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key,
                field=field
            )

            response = self.stub.HGet(request)

            if response.exists:
                print(f"✅ [Redis] Hash get successful: {key}.{field} = {response.value[:50]}...")
                return response.value
            else:
                print(f"⚠️  [Redis] Hash field not found: {key}.{field}")
                return None

        except Exception as e:
            return self.handle_error(e, "Get hash field")

    def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields"""
        try:
            self._ensure_connected()
            request = redis_service_pb2.HGetAllRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                key=key
            )

            response = self.stub.HGetAll(request)

            if response.success:
                fields = dict(response.fields)
                print(f"✅ [Redis] Hash get all successful: {key} has {len(fields)} fields")
                return fields
            else:
                print(f"⚠️  [Redis] Hash get all failed: {response.error}")
                return {}

        except Exception as e:
            return self.handle_error(e, "Get all hash fields") or {}


# Convenience usage example
if __name__ == '__main__':
    with RedisClient(host='localhost', port=50055, user_id='test_user') as client:
        # Health check
        client.health_check()

        # Basic operations
        client.set('user:1:name', 'John Doe')
        name = client.get('user:1:name')
        print(f"User name: {name}")

        # With TTL
        client.set_with_ttl('session:abc123', 'user_data', ttl_seconds=3600)
        ttl = client.ttl('session:abc123')
        print(f"Session TTL: {ttl} seconds")

        # Batch operations
        client.mset({
            'user:2:name': 'Jane Smith',
            'user:2:email': 'jane@example.com',
            'user:2:age': '25'
        })

        users = client.mget(['user:2:name', 'user:2:email', 'user:2:age'])
        print(f"Batch get: {users}")

        # Counter
        counter = client.incr('page:views')
        print(f"Page views: {counter}")

        # List operations
        client.lpush('logs', ['log1', 'log2', 'log3'])
        logs = client.lrange('logs', 0, -1)
        print(f"Log list: {logs}")

        # Hash operations
        client.hset('user:3', 'name', 'Bob Wilson')
        client.hset('user:3', 'email', 'bob@example.com')
        user_data = client.hgetall('user:3')
        print(f"User data: {user_data}")
