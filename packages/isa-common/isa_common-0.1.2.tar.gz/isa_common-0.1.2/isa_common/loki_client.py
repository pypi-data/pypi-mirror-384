#!/usr/bin/env python3
"""
Loki gRPC Client
Loki log aggregation client
"""

from typing import List, Dict, Optional
from datetime import datetime
from .base_client import BaseGRPCClient
from .proto import loki_service_pb2, loki_service_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp


class LokiClient(BaseGRPCClient):
    """Loki gRPC Client"""

    def __init__(self, host: str = 'localhost', port: int = 50054, user_id: Optional[str] = None,
                 organization_id: Optional[str] = None, lazy_connect: bool = True,
                 enable_compression: bool = True, enable_retry: bool = True):
        """
        Initialize Loki client

        Args:
            host: Service host (default: localhost)
            port: Service port (default: 50054)
            user_id: User ID
            organization_id: Organization ID
            lazy_connect: Lazy connection (default: True)
            enable_compression: Enable compression (default: True)
            enable_retry: Enable retry (default: True)
        """
        super().__init__(host, port, user_id, lazy_connect, enable_compression, enable_retry)
        self.organization_id = organization_id or 'default-org'

    def _create_stub(self):
        """Create Loki service stub"""
        return loki_service_pb2_grpc.LokiServiceStub(self.channel)

    def service_name(self) -> str:
        return "Loki"

    def health_check(self) -> Optional[Dict]:
        """Health check"""
        try:
            self._ensure_connected()
            request = loki_service_pb2.LokiHealthCheckRequest(
                user_id=self.user_id
            )
            response = self.stub.HealthCheck(request)

            print(f"✅ [Loki] Service healthy: {response.healthy}")
            print(f"   Loki status: {response.loki_status}")
            print(f"   Can write: {response.can_write}, Can read: {response.can_read}")

            return {
                'healthy': response.healthy,
                'loki_status': response.loki_status,
                'can_write': response.can_write,
                'can_read': response.can_read
            }

        except Exception as e:
            return self.handle_error(e, "Health check")

    def push_log(self, message: str, labels: Dict[str, str] = None,
                 timestamp: Optional[datetime] = None) -> Optional[Dict]:
        """Push single log entry"""
        try:
            self._ensure_connected()

            # Prepare timestamp
            ts = Timestamp()
            if timestamp:
                ts.FromDatetime(timestamp)
            else:
                ts.GetCurrentTime()

            # Prepare labels
            log_labels = labels or {}

            # Create log entry
            entry = loki_service_pb2.LogEntry(
                timestamp=ts,
                line=message,
                labels=log_labels
            )

            request = loki_service_pb2.PushLogRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                entry=entry
            )

            response = self.stub.PushLog(request)

            if response.success:
                print(f"✅ [Loki] Log pushed successfully")
                return {'success': True}
            else:
                print(f"⚠️  [Loki] Log push failed")
                return None

        except Exception as e:
            return self.handle_error(e, "Push log")

    def push_simple_log(self, message: str, service: str, level: str = 'INFO',
                       extra_labels: Dict[str, str] = None,
                       timestamp: Optional[datetime] = None) -> Optional[Dict]:
        """Push simple log (auto-add common labels)"""
        try:
            self._ensure_connected()

            # Prepare timestamp
            ts = Timestamp()
            if timestamp:
                ts.FromDatetime(timestamp)
            else:
                ts.GetCurrentTime()

            # Map log level
            level_map = {
                'DEBUG': loki_service_pb2.DEBUG,
                'INFO': loki_service_pb2.INFO,
                'WARNING': loki_service_pb2.WARNING,
                'ERROR': loki_service_pb2.ERROR,
                'CRITICAL': loki_service_pb2.CRITICAL
            }
            log_level = level_map.get(level.upper(), loki_service_pb2.INFO)

            request = loki_service_pb2.PushSimpleLogRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                timestamp=ts,
                service=service,
                level=log_level,
                message=message,
                extra_labels=extra_labels or {}
            )

            response = self.stub.PushSimpleLog(request)

            if response.success:
                print(f"✅ [Loki] Log pushed: [{level}] {message[:50]}...")
                return {'success': True}
            else:
                print(f"⚠️  [Loki] Log push failed")
                return None

        except Exception as e:
            return self.handle_error(e, "Push simple log")

    def push_log_batch(self, entries: List[Dict]) -> Optional[Dict]:
        """Push batch logs"""
        try:
            self._ensure_connected()

            log_entries = []
            for entry in entries:
                ts = Timestamp()
                if 'timestamp' in entry and entry['timestamp']:
                    ts.FromDatetime(entry['timestamp'])
                else:
                    ts.GetCurrentTime()

                log_entry = loki_service_pb2.LogEntry(
                    timestamp=ts,
                    line=entry.get('message', ''),
                    labels=entry.get('labels', {})
                )
                log_entries.append(log_entry)

            request = loki_service_pb2.PushLogBatchRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                entries=log_entries
            )

            response = self.stub.PushLogBatch(request)

            print(f"✅ [Loki] Batch push completed: {response.accepted_count} accepted, {response.rejected_count} rejected")

            return {
                'success': response.success,
                'accepted_count': response.accepted_count,
                'rejected_count': response.rejected_count,
                'errors': list(response.errors) if response.errors else []
            }

        except Exception as e:
            return self.handle_error(e, "Push log batch")

    def query_logs(self, query: str, limit: int = 100,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Dict]:
        """Query logs"""
        try:
            self._ensure_connected()

            # Prepare time range
            start_ts = Timestamp()
            end_ts = Timestamp()

            if start_time:
                start_ts.FromDatetime(start_time)
            if end_time:
                end_ts.FromDatetime(end_time)
            else:
                end_ts.GetCurrentTime()

            request = loki_service_pb2.QueryLogsRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                query=query,
                limit=limit,
                start_time=start_ts if start_time else None,
                end_time=end_ts
            )

            response = self.stub.QueryLogs(request)

            logs = []
            for entry in response.entries:
                logs.append({
                    'timestamp': entry.timestamp.ToDatetime(),
                    'message': entry.line,
                    'labels': dict(entry.labels)
                })

            print(f"✅ [Loki] Found {len(logs)} logs (total: {response.total_count})")
            return logs

        except Exception as e:
            return self.handle_error(e, "Query logs") or []

    def get_labels(self) -> List[str]:
        """Get available labels"""
        try:
            self._ensure_connected()
            request = loki_service_pb2.GetLabelsRequest(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

            response = self.stub.GetLabels(request)

            print(f"✅ [Loki] Found {len(response.labels)} labels")
            return list(response.labels)

        except Exception as e:
            return self.handle_error(e, "Get labels") or []

    def get_label_values(self, label: str) -> List[str]:
        """Get values for specific label"""
        try:
            self._ensure_connected()
            request = loki_service_pb2.GetLabelValuesRequest(
                user_id=self.user_id,
                organization_id=self.organization_id,
                label=label
            )

            response = self.stub.GetLabelValues(request)

            print(f"✅ [Loki] Label '{label}' has {len(response.values)} values")
            return list(response.values)

        except Exception as e:
            return self.handle_error(e, f"Get label values ({label})") or []

    def get_user_quota(self) -> Optional[Dict]:
        """Get user quota information"""
        try:
            self._ensure_connected()
            request = loki_service_pb2.GetUserQuotaRequest(
                user_id=self.user_id,
                organization_id=self.organization_id
            )

            response = self.stub.GetUserQuota(request)

            print(f"✅ [Loki] Quota: today used {response.today_used}/{response.daily_limit}")
            print(f"   Storage: {response.storage_used_bytes / 1024 / 1024:.2f}MB / {response.storage_limit_bytes / 1024 / 1024:.2f}MB")
            print(f"   Retention: {response.retention_days} days")

            return {
                'daily_limit': response.daily_limit,
                'today_used': response.today_used,
                'storage_limit_bytes': response.storage_limit_bytes,
                'storage_used_bytes': response.storage_used_bytes,
                'retention_days': response.retention_days,
                'quota_exceeded': response.quota_exceeded
            }

        except Exception as e:
            return self.handle_error(e, "Get user quota")


# Convenience usage example
if __name__ == '__main__':
    with LokiClient(host='localhost', port=50054, user_id='test_user') as client:
        # Health check
        client.health_check()

        # Push simple log
        client.push_simple_log(
            message="Application started successfully",
            service="my-service",
            level="INFO"
        )

        # Push log with labels
        client.push_log(
            message="User login successful",
            labels={
                "action": "login",
                "user": "john_doe",
                "ip": "192.168.1.1"
            }
        )

        # Batch push
        logs = [
            {"message": "Processing request 1", "labels": {"request_id": "req-1"}},
            {"message": "Processing request 2", "labels": {"request_id": "req-2"}},
            {"message": "Processing request 3", "labels": {"request_id": "req-3"}}
        ]
        client.push_log_batch(logs)

        # Query logs
        results = client.query_logs(query='{service="my-service"}', limit=10)
        print(f"Query results: {results}")

        # Get quota info
        quota = client.get_user_quota()
        print(f"Quota info: {quota}")
