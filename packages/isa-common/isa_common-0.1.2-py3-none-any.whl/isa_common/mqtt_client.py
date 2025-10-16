#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT gRPC Client
"""

from typing import List, Dict, Optional, Callable
from .base_client import BaseGRPCClient
from .proto import mqtt_service_pb2, mqtt_service_pb2_grpc


class MQTTClient(BaseGRPCClient):
    """MQTT gRPC client"""

    def __init__(self, host: str = 'localhost', port: int = 50053, user_id: Optional[str] = None,
                 organization_id: Optional[str] = None, lazy_connect: bool = True,
                 enable_compression: bool = True, enable_retry: bool = True):
        """
        Initialize MQTT client

        Args:
            host: Service address (default: localhost)
            port: Service port (default: 50053)
            user_id: User ID
            organization_id: Organization ID
            lazy_connect: Lazy connection (default: True)
            enable_compression: Enable compression (default: True)
            enable_retry: Enable retry (default: True)
        """
        super().__init__(host, port, user_id, lazy_connect, enable_compression, enable_retry)
        self.organization_id = organization_id or 'default-org'

    def _create_stub(self):
        """Create MQTT service stub"""
        return mqtt_service_pb2_grpc.MQTTServiceStub(self.channel)

    def service_name(self) -> str:
        return "MQTT"

    def health_check(self, deep_check: bool = False) -> Optional[Dict]:
        """Health check"""
        try:
            self._ensure_connected()
            request = mqtt_service_pb2.MQTTHealthCheckRequest(deep_check=deep_check)
            response = self.stub.HealthCheck(request)

            print(f"✅ [MQTT] Healthy: {response.healthy}")
            print(f"   Broker status: {response.broker_status}")
            print(f"   Active connections: {response.active_connections}")

            return {
                'healthy': response.healthy,
                'broker_status': response.broker_status,
                'active_connections': response.active_connections,
                'message': response.message
            }

        except Exception as e:
            return self.handle_error(e, "health check")

    def connect(self, client_id: str, username: str = '', password: str = '') -> Optional[Dict]:
        """Connect to MQTT service"""
        try:
            self._ensure_connected()
            request = mqtt_service_pb2.ConnectRequest(
                client_id=client_id,
                user_id=self.user_id,
                username=username,
                password=password
            )

            response = self.stub.Connect(request)

            if response.success:
                print(f"✅ [MQTT] Connected: {client_id}")
                print(f"   Session ID: {response.session_id}")
                return {
                    'success': True,
                    'session_id': response.session_id,
                    'message': response.message
                }
            else:
                print(f"⚠️  [MQTT] Connection failed: {response.message}")
                return None

        except Exception as e:
            return self.handle_error(e, "connect")

    def disconnect(self, session_id: str) -> Optional[Dict]:
        """Disconnect"""
        try:
            self._ensure_connected()
            request = mqtt_service_pb2.DisconnectRequest(
                session_id=session_id,
                user_id=self.user_id
            )

            response = self.stub.Disconnect(request)

            if response.success:
                print(f"✅ [MQTT] Disconnected")
                return {
                    'success': True,
                    'message': response.message
                }
            else:
                print(f"⚠️  [MQTT] Disconnect failed: {response.message}")
                return None

        except Exception as e:
            return self.handle_error(e, "disconnect")

    def publish(self, session_id: str, topic: str, payload: bytes, qos: int = 1, retained: bool = False) -> Optional[Dict]:
        """Publish message"""
        try:
            self._ensure_connected()
            request = mqtt_service_pb2.PublishRequest(
                user_id=self.user_id,
                session_id=session_id,
                topic=topic,
                payload=payload,
                qos=qos,
                retained=retained
            )

            response = self.stub.Publish(request)

            if response.success:
                print(f"✅ [MQTT] Message published: {topic}")
                return {
                    'success': True,
                    'message_id': response.message_id
                }
            else:
                print(f"⚠️  [MQTT] Publish failed: {response.message}")
                return None

        except Exception as e:
            return self.handle_error(e, "publish")

    def validate_topic(self, topic: str, allow_wildcards: bool = False) -> Optional[Dict]:
        """Validate topic name"""
        try:
            self._ensure_connected()
            request = mqtt_service_pb2.ValidateTopicRequest(
                topic=topic,
                allow_wildcards=allow_wildcards
            )

            response = self.stub.ValidateTopic(request)

            if response.valid:
                print(f"✅ [MQTT] Topic valid: {topic}")
            else:
                print(f"⚠️  [MQTT] Topic invalid: {response.message}")

            return {
                'valid': response.valid,
                'message': response.message
            }

        except Exception as e:
            return self.handle_error(e, "validate topic")

    def get_statistics(self) -> Optional[Dict]:
        """Get statistics"""
        try:
            self._ensure_connected()
            request = mqtt_service_pb2.GetStatisticsRequest(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

            response = self.stub.GetStatistics(request)

            stats = {
                'total_devices': response.total_devices,
                'online_devices': response.online_devices,
                'total_topics': response.total_topics,
                'total_subscriptions': response.total_subscriptions,
                'messages_sent_today': response.messages_sent_today,
                'messages_received_today': response.messages_received_today,
                'active_sessions': response.active_sessions
            }

            print(f"✅ [MQTT] Statistics:")
            print(f"   Total devices: {stats['total_devices']}")
            print(f"   Online devices: {stats['online_devices']}")
            print(f"   Total topics: {stats['total_topics']}")
            print(f"   Active sessions: {stats['active_sessions']}")

            return stats

        except Exception as e:
            return self.handle_error(e, "get statistics")


# Quick test
if __name__ == '__main__':
    with MQTTClient(host='localhost', port=50053, user_id='test_user', organization_id='test_org') as client:
        # Health check
        client.health_check()

        # Connect
        conn = client.connect('test-client-001')
        
        if conn:
            session_id = conn['session_id']
            
            # Validate topic
            client.validate_topic('sensors/temperature')

            # Publish message
            client.publish(session_id, 'sensors/temperature', b'25.5', qos=1)

            # Get statistics
            client.get_statistics()

            # Disconnect
            client.disconnect(session_id)
