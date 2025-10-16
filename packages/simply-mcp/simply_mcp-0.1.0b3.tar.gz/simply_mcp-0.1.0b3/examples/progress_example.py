#!/usr/bin/env python3
"""Example demonstrating progress reporting for long-running MCP operations.

This example shows how to use the progress reporting feature to provide
real-time updates during long-running tool executions.

Run with:
    python -m examples.progress_example
"""

import asyncio

from simply_mcp import BuildMCPServerServer
from simply_mcp.api.decorators import tool
from simply_mcp.core.config import SimplyMCPConfig
from simply_mcp.core.types import ProgressReporter


# Example 1: Tool with progress reporting
@tool()
async def process_large_dataset(
    num_items: int,
    progress: ProgressReporter,
) -> str:
    """Process a large dataset with progress reporting.

    Args:
        num_items: Number of items to process
        progress: Progress reporter for tracking operation progress

    Returns:
        Summary of processed items
    """
    results = []

    for i in range(num_items):
        # Calculate progress percentage
        percentage = ((i + 1) / num_items) * 100

        # Report progress with message and step counts
        await progress.update(
            percentage=percentage,
            message=f"Processing item {i + 1} of {num_items}",
            current=i + 1,
            total=num_items,
        )

        # Simulate processing work
        await asyncio.sleep(0.1)
        results.append(f"item-{i}")

    return f"Successfully processed {len(results)} items"


# Example 2: Tool with multi-stage progress
@tool()
async def multi_stage_operation(
    stages: int,
    progress: ProgressReporter,
) -> dict:
    """Perform a multi-stage operation with progress reporting.

    Args:
        stages: Number of stages to execute
        progress: Progress reporter

    Returns:
        Dictionary with stage results
    """
    stage_results = {}

    for stage in range(1, stages + 1):
        # Calculate progress for this stage
        base_percentage = ((stage - 1) / stages) * 100

        # Stage initialization
        await progress.update(
            percentage=base_percentage,
            message=f"Starting stage {stage}/{stages}",
        )
        await asyncio.sleep(0.2)

        # Stage processing
        await progress.update(
            percentage=base_percentage + (100 / stages / 2),
            message=f"Processing stage {stage}/{stages}",
        )
        await asyncio.sleep(0.3)

        # Stage completion
        await progress.update(
            percentage=base_percentage + (100 / stages),
            message=f"Completed stage {stage}/{stages}",
        )

        stage_results[f"stage_{stage}"] = f"Completed at {base_percentage + (100 / stages):.1f}%"

    return stage_results


# Example 3: Tool with optional progress (works with or without progress)
@tool()
async def flexible_operation(
    iterations: int,
    progress: ProgressReporter | None = None,
) -> str:
    """Operation that optionally reports progress.

    This tool can work with or without progress reporting, making it
    flexible for different use cases.

    Args:
        iterations: Number of iterations to perform
        progress: Optional progress reporter

    Returns:
        Summary of operation
    """
    for i in range(iterations):
        # Only report progress if reporter is available
        if progress:
            percentage = ((i + 1) / iterations) * 100
            await progress.update(
                percentage=percentage,
                message=f"Iteration {i + 1}/{iterations}",
            )

        # Simulate work
        await asyncio.sleep(0.05)

    return f"Completed {iterations} iterations"


# Example 4: Tool with error handling and progress
@tool()
async def risky_operation(
    should_fail: bool,
    progress: ProgressReporter,
) -> str:
    """Operation that may fail, demonstrating error handling with progress.

    Args:
        should_fail: Whether the operation should fail
        progress: Progress reporter

    Returns:
        Success message

    Raises:
        RuntimeError: If should_fail is True
    """
    await progress.update(25.0, message="Initializing risky operation")
    await asyncio.sleep(0.1)

    await progress.update(50.0, message="Performing critical step")
    await asyncio.sleep(0.1)

    if should_fail:
        # Progress reporter will automatically mark as failed
        raise RuntimeError("Operation failed as requested")

    await progress.update(75.0, message="Finalizing operation")
    await asyncio.sleep(0.1)

    # Progress reporter will automatically mark as complete
    return "Operation succeeded"


async def main() -> None:
    """Main function to demonstrate progress reporting."""
    print("=" * 60)
    print("Simply-MCP Progress Reporting Example")
    print("=" * 60)
    print()

    # Create server with progress enabled
    config = SimplyMCPConfig()
    config.features.enable_progress = True

    server = SimplyMCPServer(config)
    await server.initialize()

    print("Server initialized with progress reporting enabled.")
    print()
    print("Available tools:")
    print("  1. process_large_dataset - Process items with progress")
    print("  2. multi_stage_operation - Multi-stage task with progress")
    print("  3. flexible_operation - Optional progress reporting")
    print("  4. risky_operation - Error handling with progress")
    print()
    print("The server is ready to accept tool calls.")
    print("Progress updates will be logged to the console.")
    print()
    print("To test, run the server and use an MCP client to call these tools.")
    print()
    print("Example tool calls:")
    print('  {"name": "process_large_dataset", "arguments": {"num_items": 10}}')
    print('  {"name": "multi_stage_operation", "arguments": {"stages": 3}}')
    print('  {"name": "flexible_operation", "arguments": {"iterations": 5}}')
    print('  {"name": "risky_operation", "arguments": {"should_fail": false}}')
    print()

    # For demonstration purposes, let's manually test one operation
    print("Demonstrating direct tool call with progress tracking:")
    print("-" * 60)

    try:
        # Access the progress tracker
        if server.progress_tracker:
            # Create a simple callback to display progress
            async def display_progress(update: dict) -> None:
                percentage = update.get("percentage", 0)
                message = update.get("message", "")
                current = update.get("current")
                total = update.get("total")

                if current and total:
                    print(f"  [{percentage:5.1f}%] {message} ({current}/{total})")
                else:
                    print(f"  [{percentage:5.1f}%] {message}")

            # Create a progress reporter
            async with server.progress_tracker.start_operation(
                "demo-op", display_progress
            ) as progress:
                # Simulate a task
                print("\nProcessing 5 items:")
                for i in range(5):
                    await progress.update(
                        ((i + 1) / 5) * 100,
                        message=f"Processing item {i + 1}",
                        current=i + 1,
                        total=5,
                    )
                    await asyncio.sleep(0.2)

            print("\nOperation completed successfully!")
        else:
            print("Progress tracking not available (feature may be disabled)")

    except Exception as e:
        print(f"\nError during demonstration: {e}")

    print()
    print("-" * 60)
    print("Example completed. The server can now run normally.")
    print()

    # In a real scenario, you would start the server here:
    # await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
