#!/usr/bin/env python3
"""
MinIO gRPC Client
MinIO 对象存储客户端
"""

from typing import List, Dict, Optional
from .base_client import BaseGRPCClient
from .proto import minio_service_pb2, minio_service_pb2_grpc


class MinIOClient(BaseGRPCClient):
    """MinIO gRPC 客户端"""

    def __init__(self, host: str = 'localhost', port: int = 50051, user_id: Optional[str] = None,
                 lazy_connect: bool = True, enable_compression: bool = True, enable_retry: bool = True):
        """
        初始化 MinIO 客户端

        Args:
            host: 服务地址 (默认: localhost)
            port: 服务端口 (默认: 50051)
            user_id: 用户 ID
            lazy_connect: 延迟连接 (默认: True)
            enable_compression: 启用压缩 (默认: True)
            enable_retry: 启用重试 (默认: True)
        """
        super().__init__(host, port, user_id, lazy_connect, enable_compression, enable_retry)
    
    def _create_stub(self):
        """创建 MinIO service stub"""
        return minio_service_pb2_grpc.MinIOServiceStub(self.channel)
    
    def service_name(self) -> str:
        return "MinIO"
    
    def health_check(self, detailed: bool = True) -> Optional[Dict]:
        """健康检查"""
        try:
            self._ensure_connected()
            request = minio_service_pb2.HealthCheckRequest(detailed=detailed)
            response = self.stub.HealthCheck(request)
            
            print(f"✅ [MinIO] 服务状态: {response.status}")
            print(f"   健康: {response.healthy}")
            if response.details:
                print(f"   详细信息: {dict(response.details)}")
            
            return {
                'status': response.status,
                'healthy': response.healthy,
                'details': dict(response.details) if response.details else {}
            }
            
        except Exception as e:
            return self.handle_error(e, "健康检查")
    
    def create_bucket(self, bucket_name: str, organization_id: str = 'default-org',
                     region: str = 'us-east-1') -> Optional[Dict]:
        """创建存储桶"""
        try:
            self._ensure_connected()
            request = minio_service_pb2.CreateBucketRequest(
                bucket_name=bucket_name,
                user_id=self.user_id,
                organization_id=organization_id,
                region=region
            )
            
            response = self.stub.CreateBucket(request)
            
            if response.success:
                print(f"✅ [MinIO] 桶创建成功: {bucket_name}")
                return {
                    'success': True,
                    'bucket': response.bucket_info.name if response.bucket_info else bucket_name
                }
            else:
                print(f"⚠️  [MinIO] {response.message or response.error}")
                return None
            
        except Exception as e:
            return self.handle_error(e, "创建桶")
    
    def list_buckets(self, organization_id: str = 'default-org') -> List[Dict]:
        """列出存储桶"""
        try:
            self._ensure_connected()
            request = minio_service_pb2.ListBucketsRequest(
                user_id=self.user_id,
                organization_id=organization_id
            )
            
            response = self.stub.ListBuckets(request)
            
            if response.success:
                buckets = []
                for bucket in response.buckets:
                    buckets.append({
                        'name': bucket.name,
                        'owner_id': bucket.owner_id,
                        'organization_id': bucket.organization_id
                    })
                print(f"✅ [MinIO] 找到 {len(buckets)} 个桶")
                return buckets
            else:
                print(f"⚠️  [MinIO] {response.error}")
                return []
            
        except Exception as e:
            return self.handle_error(e, "列出桶") or []
    
    def upload_object(self, bucket_name: str, object_key: str, data: bytes,
                     content_type: str = 'application/octet-stream') -> Optional[Dict]:
        """上传对象 (流式)"""
        try:
            self._ensure_connected()
            def request_generator():
                # 第一个消息：元数据
                metadata = minio_service_pb2.PutObjectMetadata(
                    bucket_name=bucket_name,
                    object_key=object_key,
                    user_id=self.user_id,
                    content_type=content_type,
                    content_length=len(data)
                )
                yield minio_service_pb2.PutObjectRequest(metadata=metadata)
                
                # 后续消息：数据块
                chunk_size = 1024 * 64  # 64KB chunks
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    yield minio_service_pb2.PutObjectRequest(chunk=chunk)
            
            response = self.stub.PutObject(request_generator())
            
            if response.success:
                print(f"✅ [MinIO] 对象上传成功: {object_key}")
                return {
                    'success': True,
                    'object_key': response.object_key,
                    'size': response.size,
                    'etag': response.etag
                }
            else:
                print(f"⚠️  [MinIO] {response.error}")
                return None
            
        except Exception as e:
            return self.handle_error(e, "上传对象")
    
    def list_objects(self, bucket_name: str, prefix: str = '', max_keys: int = 100) -> List[Dict]:
        """列出对象"""
        try:
            self._ensure_connected()
            request = minio_service_pb2.ListObjectsRequest(
                bucket_name=bucket_name,
                user_id=self.user_id,
                prefix=prefix,
                max_keys=max_keys
            )
            
            response = self.stub.ListObjects(request)
            
            if response.success:
                objects = []
                for obj in response.objects:
                    objects.append({
                        'key': obj.key,
                        'size': obj.size,
                        'content_type': obj.content_type,
                        'etag': obj.etag
                    })
                print(f"✅ [MinIO] 找到 {len(objects)} 个对象")
                return objects
            else:
                print(f"⚠️  [MinIO] {response.error}")
                return []
            
        except Exception as e:
            return self.handle_error(e, "列出对象") or []
    
    def get_presigned_url(self, bucket_name: str, object_key: str,
                         expiry_seconds: int = 3600) -> Optional[str]:
        """获取预签名 URL"""
        try:
            self._ensure_connected()
            request = minio_service_pb2.GetPresignedURLRequest(
                bucket_name=bucket_name,
                object_key=object_key,
                user_id=self.user_id,
                expiry_seconds=expiry_seconds
            )
            
            response = self.stub.GetPresignedURL(request)
            
            if response.success:
                print(f"✅ [MinIO] 预签名 URL 生成成功")
                return response.url
            else:
                print(f"⚠️  [MinIO] {response.error}")
                return None
            
        except Exception as e:
            return self.handle_error(e, "获取预签名 URL")


# 便捷使用示例
if __name__ == '__main__':
    with MinIOClient(host='localhost', port=50051, user_id='test_user') as client:
        # 健康检查
        client.health_check()
        
        # 创建桶
        client.create_bucket('test-bucket')
        
        # 上传文件
        client.upload_object('test-bucket', 'test.txt', b'Hello MinIO!')
        
        # 列出对象
        objects = client.list_objects('test-bucket')
        print(f"对象: {objects}")

