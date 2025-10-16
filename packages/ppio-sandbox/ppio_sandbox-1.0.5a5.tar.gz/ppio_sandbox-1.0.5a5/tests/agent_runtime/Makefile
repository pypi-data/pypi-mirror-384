# Agent Runtime 测试 Makefile

.PHONY: help test unit integration performance compatibility examples
.PHONY: test-all test-parallel test-coverage test-report clean install-deps

# 默认目标
help:
	@echo "Agent Runtime 测试工具"
	@echo ""
	@echo "可用的命令:"
	@echo "  test-unit         运行单元测试"
	@echo "  test-integration  运行集成测试"
	@echo "  test-performance  运行性能测试"
	@echo "  test-compatibility 运行兼容性测试"
	@echo "  test-examples     运行示例测试"
	@echo "  test-all          运行所有测试"
	@echo "  test-parallel     并行运行测试"
	@echo "  test-coverage     运行测试并生成覆盖率报告"
	@echo "  test-report       生成详细测试报告"
	@echo "  lint              代码质量检查"
	@echo "  clean             清理测试输出"
	@echo "  install-deps      安装测试依赖"

# 测试命令
test-unit:
	python run_tests.py --unit --verbose

test-integration:
	python run_tests.py --integration --verbose

test-performance:
	python run_tests.py --performance --verbose

test-compatibility:
	python run_tests.py --compatibility --verbose

test-examples:
	python run_tests.py --examples --verbose

test-all:
	python run_tests.py --all --verbose

test-parallel:
	python run_tests.py --parallel --verbose

test-coverage:
	python run_tests.py --unit --coverage

test-report:
	python run_tests.py --report

# 代码质量
lint:
	python run_tests.py --lint

# 清理
clean:
	rm -rf htmlcov/
	rm -rf reports/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# 依赖安装
install-deps:
	pip install pytest pytest-asyncio pytest-mock pytest-cov
	pip install pytest-xdist pytest-benchmark pytest-html
	pip install aioresponses httpx responses
