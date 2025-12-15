"""
Blockchain Performance Analysis
Measures transaction latency, throughput, and query performance
"""
import time
import json
import statistics
from datetime import datetime
import sys
import os

# Add parent directory to path and import real client only
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'blockchain'))

try:
    from fabric_client import BlockchainClient
except Exception as e:
    print("Error: Unable to import real BlockchainClient. Ensure the 'blockchain' package is present and Fabric client code is available.")
    raise


class BlockchainBenchmark:
    """Benchmark blockchain performance"""
    
    def __init__(self):
        """Initialize benchmark with a real BlockchainClient. Will raise if client cannot be initialized."""
        try:
            self.client = BlockchainClient()
        except Exception as e:
            print("Error: Failed to initialize BlockchainClient. Make sure Fabric test-network is up and configured.")
            raise
        
        self.results = {
            'invoke_latencies': [],
            'query_latencies': [],
            'throughput': 0,
            'errors': 0
        }
    
    def benchmark_invoke(self, num_transactions=100):
        """Benchmark transaction invocation"""
        print(f"\n📊 Benchmarking {num_transactions} invoke transactions...")
        
        latencies = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(num_transactions):
            event_data = {
                'event_type': 'benchmark_test',
                'switch_id': f's{i % 10}',
                'timestamp': int(time.time()),
                'trust_score': 0.8,
                'action': f'test_action_{i}'
            }
            
            tx_start = time.time()
            try:
                success = self.client.record_event(event_data)
                tx_end = time.time()
                
                if success:
                    latency = (tx_end - tx_start) * 1000  # Convert to ms
                    latencies.append(latency)
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"Error in transaction {i}: {e}")
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{num_transactions} transactions")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        self.results['invoke_latencies'] = latencies
        self.results['errors'] = errors
        self.results['throughput'] = (num_transactions - errors) / total_duration
        
        self._print_invoke_results()
    
    def benchmark_query(self, num_queries=100):
        """Benchmark query operations"""
        print(f"\n📊 Benchmarking {num_queries} query operations...")
        
        latencies = []
        
        # First create some test data
        for i in range(10):
            event_data = {
                'event_type': 'query_benchmark',
                'switch_id': f's{i}',
                'timestamp': int(time.time()),
                'trust_score': 0.8,
                'action': 'test'
            }
            self.client.record_event(event_data)
        
        time.sleep(1)  # Allow time for data to be committed
        
        # Query benchmark
        for i in range(num_queries):
            device_id = f's{i % 10}'
            
            query_start = time.time()
            try:
                result = self.client.query_trust_log(device_id)
                query_end = time.time()
                
                latency = (query_end - query_start) * 1000
                latencies.append(latency)
            except Exception as e:
                print(f"Query error: {e}")
            
            if (i + 1) % 10 == 0:
                print(f"  Completed {i + 1}/{num_queries} queries")
        
        self.results['query_latencies'] = latencies
        self._print_query_results()
    
    def _print_invoke_results(self):
        """Print invoke benchmark results"""
        latencies = self.results['invoke_latencies']
        
        if not latencies:
            print("❌ No successful transactions")
            return
        
        print("\n" + "=" * 60)
        print("INVOKE TRANSACTION PERFORMANCE")
        print("=" * 60)
        print(f"Total Transactions: {len(latencies) + self.results['errors']}")
        print(f"Successful:         {len(latencies)}")
        print(f"Failed:             {self.results['errors']}")
        print(f"Success Rate:       {len(latencies) / (len(latencies) + self.results['errors']) * 100:.2f}%")
        print()
        print(f"Throughput:         {self.results['throughput']:.2f} TPS")
        print()
        print(f"Latency (ms):")
        print(f"  Mean:             {statistics.mean(latencies):.2f}")
        print(f"  Median:           {statistics.median(latencies):.2f}")
        print(f"  Min:              {min(latencies):.2f}")
        print(f"  Max:              {max(latencies):.2f}")
        print(f"  Std Dev:          {statistics.stdev(latencies) if len(latencies) > 1 else 0:.2f}")
        print("=" * 60)
    
    def _print_query_results(self):
        """Print query benchmark results"""
        latencies = self.results['query_latencies']
        
        if not latencies:
            print("❌ No successful queries")
            return
        
        print("\n" + "=" * 60)
        print("QUERY PERFORMANCE")
        print("=" * 60)
        print(f"Total Queries:      {len(latencies)}")
        print()
        print(f"Latency (ms):")
        print(f"  Mean:             {statistics.mean(latencies):.2f}")
        print(f"  Median:           {statistics.median(latencies):.2f}")
        print(f"  Min:              {min(latencies):.2f}")
        print(f"  Max:              {max(latencies):.2f}")
        print(f"  Std Dev:          {statistics.stdev(latencies) if len(latencies) > 1 else 0:.2f}")
        print("=" * 60)
    
    def save_results(self, filename='blockchain_benchmark.json'):
        """Save results to file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to {filename}")


def run_full_benchmark():
    """Run complete benchmark suite"""
    print("=" * 60)
    print("BLOCKCHAIN PERFORMANCE BENCHMARK")
    print("=" * 60)
    print("Mode: Real Fabric Network")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    benchmark = BlockchainBenchmark(use_mock=use_mock)
    
    # Invoke benchmark
    benchmark.benchmark_invoke(num_transactions=50)
    
    # Query benchmark
    benchmark.benchmark_query(num_queries=50)
    
    # Save results
    benchmark.save_results()
    
    print("\n✅ Benchmark completed!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Blockchain Performance Benchmark')
    parser.add_argument('--tx', type=int, default=50,
                       help='Number of transactions (default: 50)')
    parser.add_argument('--queries', type=int, default=50,
                       help='Number of queries (default: 50)')

    args = parser.parse_args()

    benchmark = BlockchainBenchmark()
    benchmark.benchmark_invoke(num_transactions=args.tx)
    benchmark.benchmark_query(num_queries=args.queries)
    benchmark.save_results()

    print("\n✅ Benchmark completed!")
