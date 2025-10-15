"""Worker start command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys

import psutil

from ...base import SyncCommand
from ...exceptions import ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse


def find_celery_workers():
    """Find running Celery worker processes."""
    workers = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'celery' in ' '.join(proc.info['cmdline']) and 'worker' in ' '.join(proc.info['cmdline']):
                workers.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return workers


@register_command("worker")
class WorkerStartCommand(SyncCommand):
    """Run Celery worker for queue processing."""
    
    name = "start"
    description = "Start Celery worker for queue processing"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'action',
            nargs='?',
            default='start',
            choices=['start', 'stop', 'restart', 'status'],
            help='Worker action (default: start)'
        )
        parser.add_argument(
            '--concurrency', '-c',
            type=int,
            default=1,
            help='Number of concurrent workers (default: 1)'
        )
        parser.add_argument(
            '--queue', '-q',
            default='gnosari-events',
            help='Queue name to process (default: gnosari-events)'
        )
        parser.add_argument(
            '--loglevel', '-l',
            default='info',
            choices=['debug', 'info', 'warning', 'error'],
            help='Log level (default: info)'
        )
    
    def execute_sync(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the worker command."""
        try:
            from ....queue.app import celery_app
            
            action = getattr(args, 'action', 'start')
            
            if action == 'status':
                workers = find_celery_workers()
                if workers:
                    self.console.print(f"Found {len(workers)} running Celery worker(s):")
                    for worker in workers:
                        try:
                            self.console.print(f"  PID: {worker.pid}, Status: {worker.status()}, CMD: {' '.join(worker.cmdline()[:5])}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                else:
                    self.console.print("No Celery workers are currently running.")
                
                return CommandResponse(
                    success=True,
                    message=f"Found {len(workers)} running workers",
                    data={"worker_count": len(workers)}
                )
            
            elif action == 'stop':
                workers = find_celery_workers()
                if workers:
                    self.console.print(f"Stopping {len(workers)} Celery worker(s)...")
                    for worker in workers:
                        try:
                            self.console.print(f"Stopping worker PID {worker.pid}...")
                            worker.terminate()
                            worker.wait(timeout=10)
                            self.console.print(f"Worker PID {worker.pid} stopped.")
                        except psutil.TimeoutExpired:
                            self.console.print(f"Worker PID {worker.pid} didn't stop gracefully, killing...")
                            worker.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            self.console.print(f"Worker PID {worker.pid} already stopped or access denied.")
                    self.console.print("All workers stopped.")
                else:
                    self.console.print("No Celery workers are currently running.")
                
                return CommandResponse(
                    success=True,
                    message="Workers stopped successfully"
                )
            
            elif action == 'restart':
                # Stop existing workers first
                workers = find_celery_workers()
                if workers:
                    self.console.print("Stopping existing workers...")
                    for worker in workers:
                        try:
                            worker.terminate()
                            worker.wait(timeout=10)
                        except psutil.TimeoutExpired:
                            worker.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                
                # Fall through to start new worker
                action = 'start'
            
            # Start worker (for start, restart actions)
            if action == 'start':
                # Build celery worker command
                worker_cmd = [
                    "celery", "-A", "gnosari.queue.app.celery_app", "worker",
                    "--concurrency", str(args.concurrency),
                    "--queues", args.queue,
                    "--loglevel", args.loglevel
                ]
                
                self.console.print(f"Starting Celery worker with command: {' '.join(worker_cmd)}")
                self.console.print(f"[dim]Concurrency: {args.concurrency}, Queue: {args.queue}, Log Level: {args.loglevel}[/dim]")
                
                try:
                    subprocess.run(worker_cmd, check=True)
                    return CommandResponse(
                        success=True,
                        message="Worker started successfully"
                    )
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Worker stopped by user[/yellow]")
                    return CommandResponse(
                        success=True,
                        message="Worker stopped by user",
                        exit_code=130
                    )
                except subprocess.CalledProcessError as e:
                    raise ConfigurationError(f"Error running worker: {e}")
            
            return CommandResponse(
                success=True,
                message=f"Worker action '{action}' completed"
            )
            
        except Exception as e:
            self.logger.error(f"Worker command failed: {e}")
            raise ConfigurationError(f"Failed to execute worker command: {e}")