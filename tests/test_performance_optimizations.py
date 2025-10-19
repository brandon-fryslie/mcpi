"""Test performance optimizations for MCPI CLI."""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mcpi.utils.performance import PerformanceOptimizer, CLIPerformanceMonitor, perf_optimizer
from mcpi.cli_optimized import OptimizedServerCatalog, CLIPerformanceEnhancer
from mcpi.registry.catalog import ServerCatalog, MCPServer


class TestPerformanceOptimizations:
    """Test performance optimization utilities."""

    def test_performance_optimizer_caching(self):
        """Test that performance optimizer caches expensive operations."""
        optimizer = PerformanceOptimizer()
        call_count = 0
        
        @optimizer.cached_operation("test_op", ttl=10)
        def expensive_operation(x):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return x * 2
        
        # First call should execute the function
        result1 = expensive_operation(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_operation(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Different parameters should execute function again
        result3 = expensive_operation(10)
        assert result3 == 20
        assert call_count == 2

    def test_performance_optimizer_cache_expiry(self):
        """Test that cached operations expire after TTL."""
        optimizer = PerformanceOptimizer()
        call_count = 0
        
        @optimizer.cached_operation("test_expiry", ttl=0.1)  # Very short TTL
        def fast_expiry_operation():
            nonlocal call_count
            call_count += 1
            return "result"
        
        # First call
        result1 = fast_expiry_operation()
        assert result1 == "result"
        assert call_count == 1
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Should execute function again
        result2 = fast_expiry_operation()
        assert result2 == "result"
        assert call_count == 2

    def test_performance_optimizer_clear_cache(self):
        """Test cache clearing functionality."""
        optimizer = PerformanceOptimizer()
        call_count = 0
        
        @optimizer.cached_operation("test_clear", ttl=60)
        def cached_operation():
            nonlocal call_count
            call_count += 1
            return "cached_result"
        
        # First call
        cached_operation()
        assert call_count == 1
        
        # Clear cache
        optimizer.clear_cache("test_clear")
        
        # Should execute function again
        cached_operation()
        assert call_count == 2

    def test_cli_performance_monitor(self):
        """Test CLI performance monitoring."""
        monitor = CLIPerformanceMonitor()
        
        # Record some command times
        monitor.record_command_time("list", 0.5)
        monitor.record_command_time("list", 0.6)
        monitor.record_command_time("search", 1.2)
        monitor.record_command_time("install", 3.0)  # Slow command
        
        # Get performance report
        report = monitor.get_performance_report()
        
        assert "command_stats" in report
        assert "slow_commands" in report
        assert "optimization_suggestions" in report
        
        # Check stats for list command
        list_stats = report["command_stats"]["list"]
        assert list_stats["execution_count"] == 2
        assert list_stats["average_time"] == 0.55
        assert list_stats["max_time"] == 0.6
        assert list_stats["min_time"] == 0.5
        
        # Check slow commands detection
        assert "install" in report["slow_commands"]
        assert report["slow_commands"]["install"] == 3.0

    def test_optimized_server_catalog_caching(self):
        """Test OptimizedServerCatalog caching functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "test_registry.yaml"
            
            # Create test registry
            registry_data = {
                "version": "1.0.0",
                "servers": [{
                    "id": "test-server",
                    "name": "Test Server",
                    "description": "Test server for optimization",
                    "category": ["testing"],
                    "author": "Test",
                    "versions": {"latest": "1.0.0"},
                    "installation": {"method": "npm", "package": "@test/server"},
                    "configuration": {"required_params": []},
                    "capabilities": ["testing"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }]
            }
            
            import yaml
            with open(registry_path, 'w') as f:
                yaml.dump(registry_data, f)
            
            # Create catalog and optimized wrapper
            catalog = ServerCatalog(registry_path=registry_path)
            optimized_catalog = OptimizedServerCatalog(catalog)
            
            # Track method calls
            with patch.object(catalog, 'list_servers', wraps=catalog.list_servers) as mock_list:
                # First call should hit the actual method
                result1 = optimized_catalog.list_servers_cached()
                assert mock_list.call_count == 1
                assert len(result1) == 1
                
                # Second call should use cache (method not called again)
                result2 = optimized_catalog.list_servers_cached()
                assert mock_list.call_count == 1  # Should not increment
                assert len(result2) == 1

    def test_cli_performance_enhancer_preload(self):
        """Test CLI performance enhancer preloading."""
        ctx_obj = {}
        
        # Mock context
        mock_ctx = Mock()
        mock_ctx.obj = ctx_obj
        
        with patch('mcpi.cli_optimized.ServerCatalog') as mock_catalog_class:
            mock_catalog = Mock()
            mock_catalog.get_categories.return_value = ["filesystem", "database"]
            mock_catalog_class.return_value = mock_catalog
            
            # Test preloading
            CLIPerformanceEnhancer.preload_common_data(mock_ctx)
            
            # Verify catalog was created and data preloaded
            assert 'catalog' in ctx_obj
            assert 'optimized_catalog' in ctx_obj
            mock_catalog.get_categories.assert_called_once()

    def test_performance_wrapper_timing(self):
        """Test performance wrapper measures execution time."""
        from mcpi.cli_optimized import performance_wrapper
        
        execution_times = []
        
        # Mock performance monitor
        original_record = CLIPerformanceMonitor.record_command_time
        def mock_record(self, command, exec_time):
            execution_times.append((command, exec_time))
        
        with patch.object(CLIPerformanceMonitor, 'record_command_time', mock_record):
            @performance_wrapper("test_command")
            def test_function():
                time.sleep(0.01)  # Small delay
                return "result"
            
            result = test_function()
            assert result == "result"
            assert len(execution_times) == 1
            assert execution_times[0][0] == "test_command"
            assert execution_times[0][1] > 0.005  # Should have measured some time

    def test_optimize_cli_startup(self):
        """Test CLI startup optimizations."""
        from mcpi.cli_optimized import optimize_cli_startup
        
        optimizations = optimize_cli_startup()
        
        assert isinstance(optimizations, dict)
        assert optimizations.get('startup_time_improved') is True
        assert optimizations.get('lazy_loading_enabled') is True
        assert optimizations.get('caching_available') is True

    def test_benchmark_cli_operations(self):
        """Test CLI operations benchmarking."""
        from mcpi.cli_optimized import benchmark_cli_operations
        
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "benchmark_registry.yaml"
            
            # Create test registry
            registry_data = {
                "version": "1.0.0",
                "servers": [{
                    "id": "filesystem",
                    "name": "Filesystem Server",
                    "description": "Filesystem operations",
                    "category": ["filesystem"],
                    "author": "Test",
                    "versions": {"latest": "1.0.0"},
                    "installation": {"method": "npm", "package": "@test/filesystem"},
                    "configuration": {"required_params": []},
                    "capabilities": ["files"],
                    "platforms": ["linux"],
                    "license": "MIT"
                }]
            }
            
            import yaml
            with open(registry_path, 'w') as f:
                yaml.dump(registry_data, f)
            
            with patch('mcpi.cli_optimized.ServerCatalog') as mock_catalog_class:
                mock_catalog = Mock()
                mock_catalog.load_registry.return_value = None
                mock_catalog.list_servers.return_value = [Mock()]
                mock_catalog.search_servers.return_value = [Mock()]
                mock_catalog_class.return_value = mock_catalog
                
                benchmarks = benchmark_cli_operations()
                
                assert isinstance(benchmarks, dict)
                assert "registry_load_time" in benchmarks
                assert "server_list_time" in benchmarks
                assert "search_time" in benchmarks

    def test_performance_tips_display(self):
        """Test performance tips display functionality."""
        from mcpi.cli_optimized import CLIPerformanceEnhancer
        
        # This should not raise any exceptions
        CLIPerformanceEnhancer.show_performance_tips()

    def test_performance_stats_collection(self):
        """Test performance statistics collection."""
        from mcpi.cli_optimized import CLIPerformanceEnhancer
        
        # Mock context with some data
        mock_ctx = Mock()
        mock_ctx.obj = {
            'catalog': Mock(),
            'optimized_catalog': Mock()
        }
        
        with patch('mcpi.cli_optimized.performance_monitor') as mock_monitor:
            mock_monitor.get_performance_report.return_value = {
                'command_stats': {},
                'slow_commands': {},
                'optimization_suggestions': []
            }
            
            stats = CLIPerformanceEnhancer.get_performance_stats(mock_ctx)
            
            assert isinstance(stats, dict)
            assert stats['cache_enabled'] is True
            assert stats['registry_loaded'] is True
            assert 'performance_monitor_stats' in stats

    def test_cached_operation_with_different_args(self):
        """Test cached operations handle different arguments correctly."""
        call_log = []
        
        @perf_optimizer.cached_operation("test_args", ttl=60)
        def operation_with_args(a, b, keyword=None):
            call_log.append((a, b, keyword))
            return f"{a}-{b}-{keyword}"
        
        # Different arguments should create separate cache entries
        result1 = operation_with_args(1, 2, keyword="test")
        result2 = operation_with_args(1, 2, keyword="test")  # Same args, should use cache
        result3 = operation_with_args(1, 3, keyword="test")  # Different args, should execute
        
        assert result1 == "1-2-test"
        assert result2 == "1-2-test"
        assert result3 == "1-3-test"
        
        # Should only have executed twice (once for each unique arg set)
        assert len(call_log) == 2
        assert call_log[0] == (1, 2, "test")
        assert call_log[1] == (1, 3, "test")