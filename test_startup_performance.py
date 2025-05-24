#!/usr/bin/env python3
"""
Test script to measure startup performance and response times
for different server implementations.
"""

import time
import subprocess
import requests
import threading
import sys
from typing import Optional

def test_server_startup(module_name: str, port: int = 8000) -> dict:
    """Test startup time and response time for a server module."""
    print(f"\n{'='*60}")
    print(f"Testing {module_name}")
    print(f"{'='*60}")
    
    # Start the server
    start_time = time.time()
    process = subprocess.Popen(
        [sys.executable, "-m", f"confluence_mcp_server.{module_name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to be ready
    server_ready = False
    startup_time = None
    
    for attempt in range(50):  # Wait up to 5 seconds
        try:
            response = requests.get(f"http://localhost:{port}/ping", timeout=0.1)
            if response.status_code == 200:
                startup_time = time.time() - start_time
                server_ready = True
                print(f"✅ Server ready in {startup_time:.3f}s")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)
    
    if not server_ready:
        process.terminate()
        return {"error": "Server failed to start"}
    
    # Test endpoint response times
    results = {
        "module": module_name,
        "startup_time": startup_time,
        "endpoints": {}
    }
    
    endpoints_to_test = [
        ("/ping", "GET"),
        ("/health", "GET"),
        ("/", "GET"),
        ("/mcp", "GET"),
    ]
    
    for endpoint, method in endpoints_to_test:
        times = []
        for _ in range(10):  # Test 10 times
            start = time.time()
            try:
                if method == "GET":
                    response = requests.get(f"http://localhost:{port}{endpoint}", timeout=1.0)
                response_time = (time.time() - start) * 1000  # Convert to ms
                times.append(response_time)
            except Exception as e:
                times.append(float('inf'))
        
        avg_time = sum(times) / len(times) if times else float('inf')
        min_time = min(times) if times else float('inf')
        max_time = max(times) if times else float('inf')
        
        results["endpoints"][endpoint] = {
            "avg_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "under_500ms": avg_time < 500,
            "under_100ms": avg_time < 100
        }
        
        status = "✅" if avg_time < 500 else "❌"
        print(f"{status} {endpoint}: {avg_time:.1f}ms avg (min: {min_time:.1f}ms, max: {max_time:.1f}ms)")
    
    # Test with config parameter
    config_test_url = f"http://localhost:{port}/mcp?config=eyJjb25mbHVlbmNlVXJsIjoidGVzdCIsInVzZXJuYW1lIjoidGVzdCIsImFwaVRva2VuIjoidGVzdCJ9"
    start = time.time()
    try:
        response = requests.get(config_test_url, timeout=1.0)
        config_time = (time.time() - start) * 1000
        results["config_test_ms"] = config_time
        status = "✅" if config_time < 500 else "❌"
        print(f"{status} /mcp with config: {config_time:.1f}ms")
    except Exception as e:
        results["config_test_ms"] = float('inf')
        print(f"❌ Config test failed: {e}")
    
    # Cleanup
    process.terminate()
    process.wait()
    
    return results

def main():
    """Test all server implementations."""
    print("🚀 Server Startup Performance Test")
    print("Testing for Smithery.ai compatibility (<500ms requirement)")
    
    servers_to_test = [
        "server_http_optimized",
        "server_ultra_minimal", 
        "server_starlette_minimal"
    ]
    
    all_results = {}
    
    for server in servers_to_test:
        try:
            results = test_server_startup(server)
            all_results[server] = results
            time.sleep(2)  # Brief pause between tests
        except KeyboardInterrupt:
            print("\n❌ Test interrupted")
            break
        except Exception as e:
            print(f"❌ Error testing {server}: {e}")
            all_results[server] = {"error": str(e)}
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY - Smithery.ai Compatibility")
    print(f"{'='*60}")
    
    for server, results in all_results.items():
        if "error" in results:
            print(f"❌ {server}: {results['error']}")
            continue
            
        startup_ok = results["startup_time"] < 5.0  # 5 second startup limit
        mcp_endpoint_ok = results["endpoints"].get("/mcp", {}).get("under_500ms", False)
        
        overall_status = "✅" if startup_ok and mcp_endpoint_ok else "❌"
        print(f"{overall_status} {server}:")
        print(f"   Startup: {results['startup_time']:.3f}s")
        print(f"   /mcp endpoint: {results['endpoints'].get('/mcp', {}).get('avg_ms', 'N/A'):.1f}ms")
        
        if startup_ok and mcp_endpoint_ok:
            print(f"   🎉 SMITHERY COMPATIBLE!")
        else:
            print(f"   ⚠️  May timeout on Smithery")

if __name__ == "__main__":
    main() 