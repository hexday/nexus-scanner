from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor, Future
import time
from enum import Enum


class TaskPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Task:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    timeout: Optional[float] = None


class ThreadManager:
    def __init__(self, max_workers: int = 10, queue_size: int = 100):
        self.logger = logging.getLogger("nexus.threading")
        self.max_workers = max_workers
        self.task_queue = queue.PriorityQueue(maxsize=queue_size)
        self.results: Dict[str, Any] = {}
        self.active_tasks: Dict[str, Future] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()
        self.running = True
        self._start_worker()

    def _start_worker(self):
        """Start worker thread for task processing"""
        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()

    def submit_task(self,
                    func: Callable,
                    *args,
                    priority: TaskPriority = TaskPriority.MEDIUM,
                    timeout: Optional[float] = None,
                    **kwargs) -> str:
        """Submit task for execution"""
        task_id = self._generate_task_id()
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout
        )

        self.task_queue.put((priority.value, task))
        return task_id

    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get task result"""
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            with self.lock:
                if task_id in self.results:
                    return self.results.pop(task_id)
            time.sleep(0.1)
        raise TimeoutError("Task result not available within timeout")

    def cancel_task(self, task_id: str) -> bool:
        """Cancel task execution"""
        with self.lock:
            if task_id in self.active_tasks:
                future = self.active_tasks[task_id]
                return future.cancel()
        return False

    def shutdown(self, wait: bool = True):
        """Shutdown thread manager"""
        self.running = False
        self.executor.shutdown(wait=wait)
        if wait:
            self.worker_thread.join()

    def _process_tasks(self):
        """Process tasks from queue"""
        while self.running:
            try:
                _, task = self.task_queue.get(timeout=1)
                future = self.executor.submit(
                    self._execute_task,
                    task
                )

                with self.lock:
                    self.active_tasks[task.id] = future

                future.add_done_callback(
                    lambda f, task_id=task.id: self._handle_completion(task_id, f)
                )

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Task processing error: {str(e)}")

    def _execute_task(self, task: Task) -> Any:
        """Execute single task"""
        try:
            if task.timeout:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(task.func, *task.args, **task.kwargs)
                    return future.result(timeout=task.timeout)
            return task.func(*task.args, **task.kwargs)
        except Exception as e:
            self.logger.error(f"Task execution error: {str(e)}")
            raise

    def _handle_completion(self, task_id: str, future: Future):
        """Handle task completion"""
        with self.lock:
            try:
                self.results[task_id] = future.result()
            except Exception as e:
                self.results[task_id] = e
            finally:
                self.active_tasks.pop(task_id, None)

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        import uuid
        return str(uuid.uuid4())

    def get_stats(self) -> Dict[str, Any]:
        """Get thread manager statistics"""
        return {
            'active_tasks': len(self.active_tasks),
            'queued_tasks': self.task_queue.qsize(),
            'completed_tasks': len(self.results),
            'worker_threads': self.max_workers
        }

    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs"""
        with self.lock:
            return list(self.active_tasks.keys())

    def clear_results(self):
        """Clear completed task results"""
        with self.lock:
            self.results.clear()
