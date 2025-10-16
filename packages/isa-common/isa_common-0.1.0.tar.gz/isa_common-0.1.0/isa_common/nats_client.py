#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NATS gRPC Client
"""

from typing import List, Dict, Optional, Callable
from .base_client import BaseGRPCClient
from .proto import nats_service_pb2, nats_service_pb2_grpc
from google.protobuf.duration_pb2 import Duration


class NATSClient(BaseGRPCClient):
    """NATS gRPC client"""

    def __init__(self, host: str = 'localhost', port: int = 50056, user_id: Optional[str] = None,
                 organization_id: Optional[str] = None, lazy_connect: bool = True,
                 enable_compression: bool = False, enable_retry: bool = True):
        """
        Initialize NATS client

        Args:
            host: Service address (default: localhost)
            port: Service port (default: 50056)
            user_id: User ID
            organization_id: Organization ID
            lazy_connect: Lazy connection (default: True)
            enable_compression: Enable compression (default: False)
            enable_retry: Enable retry (default: True)
        """
        super().__init__(host, port, user_id, lazy_connect, enable_compression, enable_retry)
        self.organization_id = organization_id or 'default-org'

    def _create_stub(self):
        """Create NATS service stub"""
        return nats_service_pb2_grpc.NATSServiceStub(self.channel)

    def service_name(self) -> str:
        return "NATS"

    def health_check(self, deep_check: bool = False) -> Optional[Dict]:
        """Health check"""
        try:
            self._ensure_connected()
            request = nats_service_pb2.NATSHealthCheckRequest(deep_check=deep_check)
            response = self.stub.HealthCheck(request)

            print(f"✅ [NATS] Healthy: {response.healthy}")
            print(f"   NATS status: {response.nats_status}")
            print(f"   JetStream enabled: {response.jetstream_enabled}")
            print(f"   Connections: {response.connections}")

            return {
                'healthy': response.healthy,
                'nats_status': response.nats_status,
                'jetstream_enabled': response.jetstream_enabled,
                'connections': response.connections,
                'message': response.message
            }

        except Exception as e:
            return self.handle_error(e, "health check")

    def publish(self, subject: str, data: bytes, headers: Optional[Dict[str, str]] = None,
                reply_to: str = '') -> Optional[Dict]:
        """Publish message to subject"""
        try:
            self._ensure_connected()
            request = nats_service_pb2.PublishRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                subject=subject,
                data=data,
                headers=headers or {},
                reply_to=reply_to
            )

            response = self.stub.Publish(request)

            if response.success:
                print(f"✅ [NATS] Message published to: {subject}")
                return {
                    'success': True,
                    'message': response.message
                }
            else:
                print(f"⚠️  [NATS] Publish failed: {response.message}")
                return None

        except Exception as e:
            return self.handle_error(e, "publish")

    def request(self, subject: str, data: bytes, timeout_seconds: int = 5) -> Optional[Dict]:
        """Request-reply pattern"""
        try:
            self._ensure_connected()
            timeout = Duration(seconds=timeout_seconds)

            request = nats_service_pb2.RequestRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                subject=subject,
                data=data,
                timeout=timeout
            )

            response = self.stub.Request(request)

            if response.success:
                print(f"✅ [NATS] Request completed: {subject}")
                return {
                    'success': True,
                    'data': response.data,
                    'subject': response.subject
                }
            else:
                print(f"⚠️  [NATS] Request failed: {response.message}")
                return None

        except Exception as e:
            return self.handle_error(e, "request")

    def get_statistics(self) -> Optional[Dict]:
        """Get statistics"""
        try:
            self._ensure_connected()
            request = nats_service_pb2.GetStatisticsRequest(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

            response = self.stub.GetStatistics(request)

            stats = {
                'total_streams': response.total_streams,
                'total_consumers': response.total_consumers,
                'total_messages': response.total_messages,
                'total_bytes': response.total_bytes,
                'connections': response.connections,
                'in_msgs': response.in_msgs,
                'out_msgs': response.out_msgs
            }

            print(f"✅ [NATS] Statistics:")
            print(f"   Total streams: {stats['total_streams']}")
            print(f"   Total consumers: {stats['total_consumers']}")
            print(f"   Total messages: {stats['total_messages']}")
            print(f"   Connections: {stats['connections']}")

            return stats

        except Exception as e:
            return self.handle_error(e, "get statistics")

    def list_streams(self) -> List[Dict]:
        """List all streams"""
        try:
            self._ensure_connected()
            request = nats_service_pb2.ListStreamsRequest(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

            response = self.stub.ListStreams(request)

            streams = []
            for stream in response.streams:
                streams.append({
                    'name': stream.name,
                    'subjects': list(stream.subjects),
                    'messages': stream.messages,
                    'bytes': stream.bytes
                })
            
            print(f"✅ [NATS] Found {len(streams)} streams")
            return streams

        except Exception as e:
            return self.handle_error(e, "list streams") or []

    def kv_put(self, bucket: str, key: str, value: bytes) -> Optional[Dict]:
        """Put value in KV store"""
        try:
            self._ensure_connected()
            request = nats_service_pb2.KVPutRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                bucket=bucket,
                key=key,
                value=value
            )

            response = self.stub.KVPut(request)

            if response.success:
                print(f"✅ [NATS] KV put: {bucket}/{key}")
                return {
                    'success': True,
                    'revision': response.revision
                }
            else:
                print(f"⚠️  [NATS] KV put failed: {response.message}")
                return None

        except Exception as e:
            return self.handle_error(e, "kv put")

    def kv_get(self, bucket: str, key: str) -> Optional[Dict]:
        """Get value from KV store"""
        try:
            self._ensure_connected()
            request = nats_service_pb2.KVGetRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                bucket=bucket,
                key=key
            )

            response = self.stub.KVGet(request)

            if response.found:
                print(f"✅ [NATS] KV get: {bucket}/{key}")
                return {
                    'found': True,
                    'value': response.value,
                    'revision': response.revision
                }
            else:
                print(f"⚠️  [NATS] KV key not found: {bucket}/{key}")
                return None

        except Exception as e:
            return self.handle_error(e, "kv get")


# Quick test
if __name__ == '__main__':
    with NATSClient(host='localhost', port=50056, user_id='test_user', 
                    organization_id='test_org', enable_compression=False) as client:
        # Health check
        client.health_check()

        # Publish
        client.publish('test.subject', b'Hello NATS!')

        # Request-reply
        client.request('test.request', b'ping', timeout_seconds=5)

        # Get statistics
        client.get_statistics()

        # JetStream - List streams
        streams = client.list_streams()
        print(f"Streams: {streams}")

        # KV Store
        client.kv_put('test-bucket', 'mykey', b'myvalue')
        result = client.kv_get('test-bucket', 'mykey')
        if result:
            print(f"KV value: {result['value']}")
