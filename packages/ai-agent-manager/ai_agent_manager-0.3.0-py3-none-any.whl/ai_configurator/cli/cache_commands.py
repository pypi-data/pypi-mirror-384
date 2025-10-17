"""
Cache management CLI commands.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..services.cached_library_service import CachedLibraryService
from ..core.config import ConfigProxy


@click.group(name="cache")
def cache_group():
    """Library cache management commands."""
    pass


@cache_group.command()
def stats():
    """Show cache statistics."""
    console = Console()
    config = ConfigProxy()
    
    cache_service = CachedLibraryService(console=console)
    stats = cache_service.get_cache_stats()
    
    # Create stats table
    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Memory Cache Size", f"{stats['memory_cache_size']}/{stats['max_memory_cache_size']}")
    table.add_row("Directory Cache Size", str(stats['directory_cache_size']))
    table.add_row("Cache TTL (hours)", str(stats['cache_ttl_hours']))
    table.add_row("Lazy Load Threshold (KB)", str(stats['lazy_load_threshold_kb']))
    
    # LRU cache info
    lru_info = stats['lru_cache_info']
    table.add_row("LRU Cache Hits", str(lru_info['hits']))
    table.add_row("LRU Cache Misses", str(lru_info['misses']))
    table.add_row("LRU Cache Size", f"{lru_info['currsize']}/{lru_info['maxsize']}")
    
    console.print(table)


@cache_group.command()
def clear():
    """Clear all caches."""
    console = Console()
    
    if click.confirm("Are you sure you want to clear all caches?"):
        cache_service = CachedLibraryService(console=console)
        cache_service.clear_cache()
    else:
        console.print("Cache clear cancelled")


@cache_group.command()
def optimize():
    """Optimize cache by removing expired entries."""
    console = Console()
    
    cache_service = CachedLibraryService(console=console)
    cache_service.optimize_cache()


@cache_group.command()
def preload():
    """Preload library files into cache."""
    console = Console()
    config = ConfigProxy()
    
    # Get library paths
    library_paths = [
        Path(config.library_path),
        Path(config._config.library_config.personal_library_path)
    ]
    
    # Add remote library if configured
    if config.remote_library_path:
        remote_path = Path(config.remote_library_path)
        if remote_path.exists():
            library_paths.append(remote_path)
    
    cache_service = CachedLibraryService(console=console)
    cache_service.preload_library(library_paths)


@cache_group.command()
@click.option("--size", "-s", type=int, help="Maximum memory cache size")
@click.option("--ttl", "-t", type=int, help="Cache TTL in hours")
@click.option("--threshold", "-th", type=int, help="Lazy load threshold in KB")
def configure(size: int, ttl: int, threshold: int):
    """Configure cache settings."""
    console = Console()
    
    cache_service = CachedLibraryService(console=console)
    
    if size:
        cache_service.max_memory_cache_size = size
        console.print(f"✅ Memory cache size set to {size}")
    
    if ttl:
        cache_service.cache_ttl_hours = ttl
        console.print(f"✅ Cache TTL set to {ttl} hours")
    
    if threshold:
        cache_service.lazy_load_threshold = threshold
        console.print(f"✅ Lazy load threshold set to {threshold} KB")
    
    if not any([size, ttl, threshold]):
        console.print("No configuration changes specified")
        console.print("Use --size, --ttl, or --threshold to modify settings")


@cache_group.command()
def benchmark():
    """Run cache performance benchmark."""
    console = Console()
    config = ConfigProxy()
    
    # Get library paths
    library_paths = [
        Path(config.library_path),
        Path(config._config.library_config.personal_library_path)
    ]
    
    if config.remote_library_path:
        remote_path = Path(config.remote_library_path)
        if remote_path.exists():
            library_paths.append(remote_path)
    
    console.print("🏃 Running cache performance benchmark...")
    
    # Test without cache
    console.print("\n📊 [bold]Test 1: Cold cache (no caching)[/bold]")
    cache_service = CachedLibraryService(console=console)
    cache_service.clear_cache()
    
    import time
    start_time = time.time()
    files_cold = cache_service.get_library_files(library_paths, force_refresh=True)
    cold_time = time.time() - start_time
    
    # Test with warm cache
    console.print("\n📊 [bold]Test 2: Warm cache (cached)[/bold]")
    start_time = time.time()
    files_warm = cache_service.get_library_files(library_paths, force_refresh=False)
    warm_time = time.time() - start_time
    
    # Display results
    console.print(f"\n📈 [bold]Benchmark Results[/bold]")
    
    results_table = Table()
    results_table.add_column("Test", style="cyan")
    results_table.add_column("Files", style="white")
    results_table.add_column("Time (s)", style="green")
    results_table.add_column("Files/sec", style="yellow")
    
    cold_fps = len(files_cold) / cold_time if cold_time > 0 else 0
    warm_fps = len(files_warm) / warm_time if warm_time > 0 else 0
    
    results_table.add_row("Cold Cache", str(len(files_cold)), f"{cold_time:.3f}", f"{cold_fps:.1f}")
    results_table.add_row("Warm Cache", str(len(files_warm)), f"{warm_time:.3f}", f"{warm_fps:.1f}")
    
    console.print(results_table)
    
    # Calculate speedup
    if cold_time > 0 and warm_time > 0:
        speedup = cold_time / warm_time
        console.print(f"\n🚀 Cache speedup: {speedup:.1f}x faster")
    
    # Show cache stats
    stats = cache_service.get_cache_stats()
    console.print(f"\n💾 Cache efficiency: {stats['lru_cache_info']['hits']} hits, "
                 f"{stats['lru_cache_info']['misses']} misses")


def register_cache_commands(cli):
    """Register cache commands with the main CLI."""
    cli.add_command(cache_group)
