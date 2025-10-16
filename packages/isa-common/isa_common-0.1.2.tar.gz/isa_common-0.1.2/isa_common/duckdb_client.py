#!/usr/bin/env python3
"""
DuckDB gRPC Client
DuckDB OLAP 数据分析客户端
"""

from typing import List, Dict, Any, Optional
from google.protobuf import struct_pb2

from .base_client import BaseGRPCClient
from .proto import duckdb_service_pb2, duckdb_service_pb2_grpc, common_pb2


class DuckDBClient(BaseGRPCClient):
    """DuckDB gRPC 客户端"""

    def __init__(self, host: str = 'localhost', port: int = 50052, user_id: Optional[str] = None,
                 lazy_connect: bool = True, enable_compression: bool = True, enable_retry: bool = True):
        """
        初始化 DuckDB 客户端

        Args:
            host: 服务地址 (默认: localhost)
            port: 服务端口 (默认: 50052)
            user_id: 用户 ID
            lazy_connect: 延迟连接 (默认: True)
            enable_compression: 启用压缩 (默认: True)
            enable_retry: 启用重试 (默认: True)
        """
        super().__init__(host, port, user_id, lazy_connect, enable_compression, enable_retry)
    
    def _create_stub(self):
        """创建 DuckDB service stub"""
        return duckdb_service_pb2_grpc.DuckDBServiceStub(self.channel)
    
    def service_name(self) -> str:
        return "DuckDB"
    
    def _get_org_id(self) -> str:
        """获取组织ID"""
        return 'default_org'
    
    # ========================================
    # 数据库管理
    # ========================================
    
    def create_database(self, db_name: str, minio_bucket: str = '', metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        创建数据库

        Args:
            db_name: 数据库名称
            minio_bucket: MinIO bucket for data storage
            metadata: Metadata dict

        Returns:
            是否成功
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.CreateDatabaseRequest(
                database_name=db_name,
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                minio_bucket=minio_bucket,
                metadata=metadata or {},
            )
            
            response = self.stub.CreateDatabase(request)
            
            if response.success:
                print(f"✅ [DuckDB] 数据库创建成功: {db_name}")
                return True
            else:
                print(f"❌ [DuckDB] 数据库创建失败: {response.error}")
                return False
                
        except Exception as e:
            return self.handle_error(e, "创建数据库") or False
    
    def list_databases(self) -> List[Dict]:
        """
        列出所有数据库

        Returns:
            数据库列表
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.ListDatabasesRequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
            )
            
            response = self.stub.ListDatabases(request)
            
            if response.success:
                databases = []
                for db in response.databases:
                    databases.append({
                        'name': db.database_name,
                        'size': db.size_bytes,
                        'table_count': db.table_count,
                        'created_at': str(db.created_at),
                    })
                print(f"✅ [DuckDB] 找到 {len(databases)} 个数据库")
                return databases
            else:
                print(f"❌ [DuckDB] 列出数据库失败: {response.error}")
                return []
                
        except Exception as e:
            return self.handle_error(e, "列出数据库") or []
    
    # ========================================
    # 查询操作
    # ========================================
    
    def execute_query(self, db_name: str, sql: str, limit: int = 100) -> List[Dict]:
        """
        执行 SQL 查询

        Args:
            db_name: 数据库名称
            sql: SQL 查询语句
            limit: 返回结果限制

        Returns:
            查询结果列表
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.ExecuteQueryRequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                database_name=db_name,
                sql=sql,
                limit=limit,
            )
            
            response = self.stub.ExecuteQuery(request)
            
            if response.success:
                # 转换结果
                results = []
                for row in response.rows:
                    results.append(dict(row))
                
                print(f"✅ [DuckDB] 查询成功，返回 {len(results)} 条记录")
                return results
            else:
                print(f"❌ [DuckDB] 查询失败: {response.error}")
                return []
                
        except Exception as e:
            return self.handle_error(e, "执行查询") or []
    
    def execute_statement(self, db_name: str, sql: str) -> int:
        """
        执行写操作 (INSERT/UPDATE/DELETE)

        Args:
            db_name: 数据库名称
            sql: SQL 语句

        Returns:
            影响的行数
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.ExecuteStatementRequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                database_name=db_name,
                sql=sql,
            )
            
            response = self.stub.ExecuteStatement(request)
            
            if response.success:
                print(f"✅ [DuckDB] 语句执行成功，影响 {response.rows_affected} 行")
                return response.rows_affected
            else:
                print(f"❌ [DuckDB] 语句执行失败: {response.error}")
                return 0
                
        except Exception as e:
            return self.handle_error(e, "执行语句") or 0
    
    # ========================================
    # 表管理
    # ========================================
    
    def create_table(self, db_name: str, table_name: str, schema: Dict[str, str]) -> bool:
        """
        创建表

        Args:
            db_name: 数据库名称
            table_name: 表名
            schema: 列定义 {'column_name': 'data_type'}

        Returns:
            是否成功
        """
        try:
            self._ensure_connected()
            columns = [
                duckdb_service_pb2.ColumnDefinition(
                    name=name,
                    data_type=dtype,
                )
                for name, dtype in schema.items()
            ]
            
            request = duckdb_service_pb2.CreateTableRequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                database_name=db_name,
                table_name=table_name,
                columns=columns,
            )
            
            response = self.stub.CreateTable(request)
            
            if response.success:
                print(f"✅ [DuckDB] 表创建成功: {table_name}")
                return True
            else:
                print(f"❌ [DuckDB] 表创建失败: {response.error}")
                return False
                
        except Exception as e:
            return self.handle_error(e, "创建表") or False
    
    def list_tables(self, db_name: str) -> List[str]:
        """
        列出所有表

        Args:
            db_name: 数据库名称

        Returns:
            表名列表
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.ListTablesRequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                database_name=db_name,
            )
            
            response = self.stub.ListTables(request)
            
            if response.success:
                tables = [table.table_name for table in response.tables]
                print(f"✅ [DuckDB] 找到 {len(tables)} 个表")
                return tables
            else:
                print(f"❌ [DuckDB] 列出表失败: {response.error}")
                return []
                
        except Exception as e:
            return self.handle_error(e, "列出表") or []
    
    # ========================================
    # 数据导入/导出
    # ========================================
    
    def import_from_minio(self, db_name: str, table_name: str,
                         bucket: str, object_key: str,
                         file_format: str = 'parquet') -> bool:
        """
        从 MinIO 导入数据

        Args:
            db_name: 数据库名称
            table_name: 目标表名
            bucket: MinIO 桶名
            object_key: 对象键
            file_format: 文件格式 (parquet/csv/json)

        Returns:
            是否成功
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.ImportFromMinIORequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                database_name=db_name,
                table_name=table_name,
                bucket_name=bucket,
                object_key=object_key,
                file_format=file_format,
            )
            
            response = self.stub.ImportFromMinIO(request)
            
            if response.success:
                print(f"✅ [DuckDB] 数据导入成功，导入 {response.rows_imported} 行")
                return True
            else:
                print(f"❌ [DuckDB] 数据导入失败: {response.error}")
                return False
                
        except Exception as e:
            return self.handle_error(e, "从MinIO导入") or False
    
    def query_minio_file(self, db_name: str, bucket: str,
                        object_key: str, file_format: str = 'parquet',
                        limit: int = 100) -> List[Dict]:
        """
        直接查询 MinIO 中的文件（无需导入）

        Args:
            db_name: 数据库名称
            bucket: MinIO 桶名
            object_key: 对象键
            file_format: 文件格式
            limit: 返回结果限制

        Returns:
            查询结果
        """
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.QueryMinIOFileRequest(
                user_id=self.user_id,
                organization_id=self._get_org_id(),
                database_name=db_name,
                bucket_name=bucket,
                object_key=object_key,
                file_format=file_format,
                limit=limit,
            )
            
            response = self.stub.QueryMinIOFile(request)
            
            if response.success:
                results = []
                for row in response.rows:
                    results.append(dict(row))
                
                print(f"✅ [DuckDB] MinIO文件查询成功，返回 {len(results)} 条记录")
                return results
            else:
                print(f"❌ [DuckDB] MinIO文件查询失败: {response.error}")
                return []
                
        except Exception as e:
            return self.handle_error(e, "查询MinIO文件") or []
    
    # ========================================
    # 健康检查
    # ========================================
    
    def health_check(self, detailed: bool = False) -> bool:
        """健康检查"""
        try:
            self._ensure_connected()
            request = duckdb_service_pb2.HealthCheckRequest(
                detailed=detailed,
            )
            
            response = self.stub.HealthCheck(request)
            
            if response.healthy:
                print(f"✅ [DuckDB] 服务健康")
                print(f"   状态: {response.status}")
                if response.details:
                    print(f"   详情: {dict(response.details)}")
                return True
            else:
                print(f"❌ [DuckDB] 服务不健康: {response.status}")
                return False
                
        except Exception as e:
            print(f"❌ [DuckDB] 健康检查失败: {e}")
            return False


# 便捷使用示例
if __name__ == '__main__':
    # 使用 with 语句自动管理连接
    with DuckDBClient(host='localhost', port=50052, user_id='test_user') as client:
        # 健康检查
        client.health_check()
        
        # 数据库操作
        client.create_database('analytics', 'Analytics database')
        databases = client.list_databases()
        print(f"数据库列表: {databases}")
        
        # 查询操作
        results = client.execute_query('analytics', 'SELECT * FROM users LIMIT 10')
        print(f"查询结果: {results}")

