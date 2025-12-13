"""Performance benchmarking for mcp-switchboard components."""
import time
import statistics
from typing import List, Dict, Any
from mcp_switchboard.analyzer.parser import TaskParser
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry
from mcp_switchboard.cache import TaskCache


def benchmark(func, iterations: int = 100) -> Dict[str, float]:
    """Run benchmark and return statistics."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0
    }


def benchmark_task_parser():
    """Benchmark task parsing."""
    parser = TaskParser()
    task = "Deploy ECS service to prod Tokyo using Jira DEVOPS-123"
    
    def run():
        parser.parse(task)
    
    return benchmark(run)


def benchmark_task_analyzer():
    """Benchmark task analysis."""
    analyzer = TaskAnalyzer()
    task = "Deploy ECS service to prod Tokyo using Jira DEVOPS-123"
    
    def run():
        analyzer.analyze(task)
    
    return benchmark(run)


def benchmark_server_selector():
    """Benchmark server selection."""
    registry = ServerRegistry()
    selector = ServerSelector(registry)
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze("Deploy ECS service to prod Tokyo using Jira DEVOPS-123")
    
    def run():
        selector.select(analysis)
    
    return benchmark(run)


def benchmark_task_cache():
    """Benchmark task caching."""
    cache = TaskCache(ttl_hours=24)
    analysis_dict = {
        "aws_account": "prod",
        "aws_region": "ap-northeast-1",
        "jira_ticket": "DEVOPS-123"
    }
    
    def run():
        fingerprint = cache.generate_fingerprint(analysis_dict)
        cache.set(fingerprint, {"test": "data"})
        cache.get(fingerprint)
    
    return benchmark(run)


def run_all_benchmarks() -> Dict[str, Dict[str, float]]:
    """Run all benchmarks and return results."""
    print("Running performance benchmarks...\n")
    
    results = {}
    
    print("1. Task Parser...")
    results["task_parser"] = benchmark_task_parser()
    
    print("2. Task Analyzer...")
    results["task_analyzer"] = benchmark_task_analyzer()
    
    print("3. Server Selector...")
    results["server_selector"] = benchmark_server_selector()
    
    print("4. Task Cache...")
    results["task_cache"] = benchmark_task_cache()
    
    return results


def print_results(results: Dict[str, Dict[str, float]]):
    """Print benchmark results in readable format."""
    print("\n" + "="*70)
    print("PERFORMANCE BENCHMARK RESULTS")
    print("="*70)
    
    # Performance targets from spec
    targets = {
        "task_analyzer": 2000,  # < 2 seconds
        "server_selector": 500,  # < 500ms
    }
    
    for component, stats in results.items():
        print(f"\n{component.replace('_', ' ').title()}:")
        print(f"  Mean:   {stats['mean']:.2f} ms")
        print(f"  Median: {stats['median']:.2f} ms")
        print(f"  Min:    {stats['min']:.2f} ms")
        print(f"  Max:    {stats['max']:.2f} ms")
        print(f"  StdDev: {stats['stdev']:.2f} ms")
        
        # Check against targets
        if component in targets:
            target = targets[component]
            status = "✓ PASS" if stats['mean'] < target else "✗ FAIL"
            print(f"  Target: < {target} ms - {status}")
    
    # Calculate total orchestration time (excluding credential renewal)
    total = (
        results["task_analyzer"]["mean"] +
        results["server_selector"]["mean"]
    )
    
    print(f"\n{'='*70}")
    print(f"Total Orchestration Time (excluding credentials): {total:.2f} ms")
    print(f"Target: < 10,000 ms - {'✓ PASS' if total < 10000 else '✗ FAIL'}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    results = run_all_benchmarks()
    print_results(results)
