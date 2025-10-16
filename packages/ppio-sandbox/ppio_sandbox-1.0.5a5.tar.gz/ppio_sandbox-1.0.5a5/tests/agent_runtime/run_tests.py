#!/usr/bin/env python3
"""
Agent Runtime 模块测试执行脚本

提供不同层级和类型的测试执行选项，支持生成详细的测试报告。
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """测试执行器"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.runtime_dir = test_dir / "runtime"
        self.client_dir = test_dir / "client"
        
    def run_command(self, cmd: List[str], description: str) -> bool:
        """执行命令并显示结果"""
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print(f"{'='*60}")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 60)
        
        try:
            # 修改为使用 poetry run 前缀，并直接运行
            if cmd[0] == "python":
                cmd = ["poetry", "run"] + cmd
            result = subprocess.run(cmd, cwd=self.test_dir.parent)
            
            if result.returncode == 0:
                print(f"✅ {description} - PASSED")
                return True
            else:
                print(f"❌ {description} - FAILED (exit code: {result.returncode})")
                return False
        except Exception as e:
            print(f"❌ {description} - ERROR: {e}")
            return False
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """运行单元测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/runtime/unit/", "-m", "unit"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=ppio_sandbox.agent_runtime.runtime",
                "--cov-report=html:htmlcov/runtime_unit",
                "--cov-report=term-missing"
            ])
        
        return self.run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """运行集成测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/runtime/integration/", "-m", "integration"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd, "Integration Tests")
    
    
    def run_compatibility_tests(self, verbose: bool = False) -> bool:
        """运行兼容性测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/runtime/compatibility/", "-m", "compatibility"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd, "Compatibility Tests")
    
    def run_examples_tests(self, verbose: bool = False) -> bool:
        """运行示例测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/examples/"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd, "Examples Tests")
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = False, module: str = "all") -> bool:
        """运行所有测试
        
        Args:
            module: 测试模块 ("runtime", "client", "all")
        """
        if module == "runtime":
            cmd = ["python", "-m", "pytest", "tests/agent_runtime/runtime/"]
            cov_source = "ppio_sandbox.agent_runtime.runtime"
            report_dir = "htmlcov/runtime_full"
        elif module == "client":
            cmd = ["python", "-m", "pytest", "tests/agent_runtime/client/"]
            cov_source = "ppio_sandbox.agent_runtime.client"
            report_dir = "htmlcov/client_full"
        else:  # "all"
            cmd = ["python", "-m", "pytest", "tests/agent_runtime/"]
            cov_source = "ppio_sandbox.agent_runtime"
            report_dir = "htmlcov/agent_runtime_full"
        
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                f"--cov={cov_source}",
                f"--cov-report=html:{report_dir}",
                "--cov-report=term-missing",
                "--cov-fail-under=85"
            ])
        
        description = f"All {module.title()} Tests" if module != "all" else "All Agent Runtime Tests"
        return self.run_command(cmd, description)
    
    def run_specific_file(self, file_path: str, verbose: bool = False) -> bool:
        """运行特定测试文件"""
        cmd = ["python", "-m", "pytest", file_path]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd, f"Tests in {file_path}")
    
    # === Client Tests ===
    def run_client_unit_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """运行客户端单元测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/client/unit/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=ppio_sandbox.agent_runtime.client",
                "--cov-report=html:htmlcov/client_unit",
                "--cov-report=term-missing"
            ])
        
        return self.run_command(cmd, "Client Unit Tests")
    
    def run_client_integration_tests(self, verbose: bool = False) -> bool:
        """运行客户端集成测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/client/integration/"]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd, "Client Integration Tests")
    
    
    def run_all_client_tests(self, verbose: bool = False, coverage: bool = False) -> bool:
        """运行所有客户端测试"""
        cmd = ["python", "-m", "pytest", "tests/agent_runtime/client/"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=ppio_sandbox.agent_runtime.client",
                "--cov-report=html:htmlcov/client_full",
                "--cov-report=term-missing",
                "--cov-fail-under=90"
            ])
        
        return self.run_command(cmd, "All Client Tests")
    
    def run_parallel_tests(self, workers: int = 4, verbose: bool = False, module: str = "all") -> bool:
        """并行运行测试"""
        if module == "runtime":
            test_path = "tests/agent_runtime/runtime/"
        elif module == "client":
            test_path = "tests/agent_runtime/client/"
        else:  # "all"
            test_path = "tests/agent_runtime/"
        
        cmd = [
            "python", "-m", "pytest", 
            test_path,
            "-n", str(workers),
        ]
        
        if verbose:
            cmd.append("-v")
        
        description = f"Parallel {module.title()} Tests" if module != "all" else "Parallel Agent Runtime Tests"
        return self.run_command(cmd, f"{description} (workers: {workers})")
    
    def generate_test_report(self, module: str = "all") -> bool:
        """生成详细的测试报告"""
        if module == "runtime":
            test_path = "tests/agent_runtime/runtime/"
            cov_source = "ppio_sandbox.agent_runtime.runtime"
            report_prefix = "runtime"
        elif module == "client":
            test_path = "tests/agent_runtime/client/"
            cov_source = "ppio_sandbox.agent_runtime.client"
            report_prefix = "client"
        else:  # "all"
            test_path = "tests/agent_runtime/"
            cov_source = "ppio_sandbox.agent_runtime"
            report_prefix = "agent_runtime"
        
        cmd = [
            "python", "-m", "pytest",
            test_path,
            f"--html=reports/{report_prefix}_report.html",
            "--self-contained-html",
            f"--junitxml=reports/{report_prefix}_junit.xml",
            f"--cov={cov_source}",
            f"--cov-report=html:reports/{report_prefix}_coverage_html",
            f"--cov-report=xml:reports/{report_prefix}_coverage.xml"
        ]
        
        # 创建报告目录
        reports_dir = self.test_dir.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        description = f"Generate {module.title()} Test Report" if module != "all" else "Generate Complete Test Report"
        return self.run_command(cmd, description)
    
    def lint_and_format_check(self) -> bool:
        """代码质量检查"""
        results = []
        
        # 检查代码格式 - Runtime
        results.append(self.run_command(
            ["python", "-m", "ruff", "check", "src/ppio_sandbox/agent_runtime/runtime/"],
            "Ruff Code Quality Check (Runtime)"
        ))
        
        # 检查代码格式 - Client
        results.append(self.run_command(
            ["python", "-m", "ruff", "check", "src/ppio_sandbox/agent_runtime/client/"],
            "Ruff Code Quality Check (Client)"
        ))
        
        # 类型检查 - Runtime
        results.append(self.run_command(
            ["python", "-m", "mypy", "src/ppio_sandbox/agent_runtime/runtime/"],
            "MyPy Type Check (Runtime)"
        ))
        
        # 类型检查 - Client
        results.append(self.run_command(
            ["python", "-m", "mypy", "src/ppio_sandbox/agent_runtime/client/"],
            "MyPy Type Check (Client)"
        ))
        
        return all(results)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Agent Runtime 模块测试执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
测试执行示例:

  # 运行所有单元测试
  python run_tests.py --unit

  # 运行集成测试（带详细输出）
  python run_tests.py --integration --verbose

  # 运行所有测试（带覆盖率报告）
  python run_tests.py --all --coverage

  # 并行运行测试
  python run_tests.py --parallel

  # 生成完整测试报告
  python run_tests.py --report

  # 运行特定测试文件
  python run_tests.py --file tests/agent_runtime/runtime/unit/test_models.py

  # 代码质量检查
  python run_tests.py --lint
        """
    )
    
    # 测试类型选项
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument("--unit", action="store_true", help="运行单元测试")
    test_group.add_argument("--integration", action="store_true", help="运行集成测试")
    test_group.add_argument("--compatibility", action="store_true", help="运行兼容性测试")
    test_group.add_argument("--examples", action="store_true", help="运行示例测试")
    test_group.add_argument("--all", action="store_true", help="运行所有测试")
    test_group.add_argument("--parallel", action="store_true", help="并行运行测试")
    test_group.add_argument("--report", action="store_true", help="生成测试报告")
    test_group.add_argument("--file", type=str, help="运行特定测试文件")
    test_group.add_argument("--lint", action="store_true", help="代码质量检查")
    
    # 客户端特定测试选项
    test_group.add_argument("--client-unit", action="store_true", help="运行客户端单元测试")
    test_group.add_argument("--client-integration", action="store_true", help="运行客户端集成测试")
    test_group.add_argument("--client-all", action="store_true", help="运行所有客户端测试")
    
    # 选项参数
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--workers", type=int, default=4, help="并行测试工作进程数")
    parser.add_argument("--module", choices=["runtime", "client", "all"], default="runtime", 
                       help="指定测试模块 (runtime/client/all)")
    parser.add_argument("--network", action="store_true", help="包含需要网络的测试")
    
    args = parser.parse_args()
    
    # 确定测试目录
    test_dir = Path(__file__).parent
    if not test_dir.exists():
        print(f"❌ 测试目录不存在: {test_dir}")
        sys.exit(1)
    
    # 创建测试执行器
    runner = TestRunner(test_dir)
    
    # 执行相应的测试
    success = False
    
    if args.unit:
        success = runner.run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.integration:
        success = runner.run_integration_tests(verbose=args.verbose)
    elif args.compatibility:
        success = runner.run_compatibility_tests(verbose=args.verbose)
    elif args.examples:
        success = runner.run_examples_tests(verbose=args.verbose)
    elif args.all:
        success = runner.run_all_tests(
            verbose=args.verbose, 
            coverage=args.coverage,
            module=args.module
        )
    elif args.parallel:
        success = runner.run_parallel_tests(workers=args.workers, verbose=args.verbose, module=args.module)
    elif args.report:
        success = runner.generate_test_report(module=args.module)
    elif args.file:
        success = runner.run_specific_file(args.file, verbose=args.verbose)
    elif args.lint:
        success = runner.lint_and_format_check()
    # 客户端特定测试
    elif args.client_unit:
        success = runner.run_client_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.client_integration:
        success = runner.run_client_integration_tests(verbose=args.verbose)
    elif args.client_all:
        success = runner.run_all_client_tests(
            verbose=args.verbose, 
            coverage=args.coverage
        )
    
    # 输出结果
    if success:
        print(f"\n🎉 测试执行成功!")
        sys.exit(0)
    else:
        print(f"\n💥 测试执行失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
