"""
MRCE+ Task Runner

This module provides functionality to run tasks in the MRCE+ multi-agent system.
It manages the execution of tasks through the coordinator and collects results.
"""

import json
import logging
import time
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

class TaskRunner:
    """
    TaskRunner handles the execution of tasks in the MRCE+ system.
    
    It provides interfaces for submitting tasks, tracking their progress,
    and collecting and analyzing results.
    """
    
    def __init__(
        self,
        coordinator,
        metrics_collector=None,
        max_concurrent_tasks: int = 5,
        results_dir: str = "./task_results"
    ):
        """
        Initialize the task runner.
        
        Args:
            coordinator: The MRCE+ coordinator instance
            metrics_collector: Optional metrics collector for monitoring
            max_concurrent_tasks: Maximum number of tasks to run concurrently
            results_dir: Directory to save task results
        """
        self.coordinator = coordinator
        self.metrics_collector = metrics_collector
        self.max_concurrent_tasks = max_concurrent_tasks
        self.results_dir = results_dir
        
        # Ensure results directory exists
        os.makedirs(results_dir, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Track running and completed tasks
        self.running_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}
        
        self.logger.info(f"TaskRunner initialized with max {max_concurrent_tasks} concurrent tasks")
        
    def run_task(self, task: Dict) -> str:
        """
        Submit a task for execution.
        
        Args:
            task: Task definition dictionary
            
        Returns:
            Task ID for tracking
        """
        # Generate task ID if not provided
        if "id" not in task:
            task["id"] = str(uuid.uuid4())
            
        task_id = task["id"]
        
        # Check if we can run more tasks
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            self.logger.warning(f"Max concurrent tasks reached ({self.max_concurrent_tasks}), task {task_id} queued")
            # In a real implementation, we would queue the task
            # For simplicity, we'll just run it anyway
            
        # Update task status
        task["status"] = "running"
        task["start_time"] = datetime.now().isoformat()
        
        self.running_tasks[task_id] = task
        self.logger.info(f"Starting task {task_id}: {task.get('description', 'No description')}")
        
        try:
            # Run the task using the coordinator
            start_time = time.time()
            
            # The actual execution through the coordinator
            result = self.coordinator.execute_task(task)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update task with result
            task["status"] = "completed"
            task["end_time"] = datetime.now().isoformat()
            task["execution_time"] = execution_time
            task["result"] = result
            
            # Move from running to completed
            del self.running_tasks[task_id]
            self.completed_tasks[task_id] = task
            
            # Record metrics if available
            if self.metrics_collector:
                self.metrics_collector.record_task_execution(
                    task_type=task.get("type", "unknown"),
                    duration=execution_time,
                    success=True
                )
                
            # Save task result
            self._save_task_result(task)
            
            self.logger.info(f"Task {task_id} completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            # Handle task failure
            task["status"] = "failed"
            task["end_time"] = datetime.now().isoformat()
            task["error"] = str(e)
            
            # Move from running to failed
            del self.running_tasks[task_id]
            self.failed_tasks[task_id] = task
            
            # Record metrics if available
            if self.metrics_collector:
                execution_time = time.time() - start_time
                self.metrics_collector.record_task_execution(
                    task_type=task.get("type", "unknown"),
                    duration=execution_time,
                    success=False,
                    error=str(e)
                )
                
            # Save task result even if failed
            self._save_task_result(task)
            
            self.logger.error(f"Task {task_id} failed: {e}")
            
        return task_id
            
    def run_batch(self, tasks: List[Dict]) -> List[str]:
        """
        Run a batch of tasks sequentially.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            List of task IDs
        """
        task_ids = []
        
        for task in tasks:
            task_id = self.run_task(task)
            task_ids.append(task_id)
            
        return task_ids
        
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        Get the current status of a task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Task status dictionary or None if not found
        """
        if task_id in self.running_tasks:
            return {
                "id": task_id,
                "status": "running",
                "start_time": self.running_tasks[task_id].get("start_time")
            }
        elif task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "id": task_id,
                "status": "completed",
                "start_time": task.get("start_time"),
                "end_time": task.get("end_time"),
                "execution_time": task.get("execution_time")
            }
        elif task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                "id": task_id,
                "status": "failed",
                "start_time": task.get("start_time"),
                "end_time": task.get("end_time"),
                "error": task.get("error")
            }
        else:
            return None
            
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task result or None if not completed or found
        """
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].get("result")
        else:
            return None
            
    def get_all_task_statuses(self) -> Dict[str, Dict]:
        """
        Get statuses of all tasks.
        
        Returns:
            Dictionary mapping task IDs to status dictionaries
        """
        statuses = {}
        
        # Running tasks
        for task_id in self.running_tasks:
            statuses[task_id] = self.get_task_status(task_id)
            
        # Completed tasks
        for task_id in self.completed_tasks:
            statuses[task_id] = self.get_task_status(task_id)
            
        # Failed tasks
        for task_id in self.failed_tasks:
            statuses[task_id] = self.get_task_status(task_id)
            
        return statuses
        
    def summarize_results(self) -> Dict:
        """
        Summarize task execution results.
        
        Returns:
            Dictionary of summary statistics
        """
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks) + len(self.running_tasks)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        running_count = len(self.running_tasks)
        
        # Calculate success rate
        success_rate = 0
        if completed_count + failed_count > 0:
            success_rate = (completed_count / (completed_count + failed_count)) * 100
            
        # Calculate average execution time
        avg_execution_time = 0
        if completed_count > 0:
            total_time = sum(task.get("execution_time", 0) for task in self.completed_tasks.values())
            avg_execution_time = total_time / completed_count
            
        # Count by task type
        task_type_counts = {}
        for task in list(self.completed_tasks.values()) + list(self.failed_tasks.values()):
            task_type = task.get("type", "unknown")
            if task_type not in task_type_counts:
                task_type_counts[task_type] = {"completed": 0, "failed": 0}
                
            if task["status"] == "completed":
                task_type_counts[task_type]["completed"] += 1
            else:
                task_type_counts[task_type]["failed"] += 1
                
        return {
            "total_tasks": total_tasks,
            "completed": completed_count,
            "failed": failed_count,
            "running": running_count,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "by_task_type": task_type_counts
        }
        
    def _save_task_result(self, task: Dict):
        """Save a task result to the results directory."""
        task_id = task["id"]
        
        # Create filename with task ID
        filename = f"{task_id}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(task, f, indent=2)
                
            self.logger.debug(f"Task {task_id} result saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save task {task_id} result: {e}")
            
    def export_all_results(self, filepath: str):
        """
        Export all task results to a single file.
        
        Args:
            filepath: Path to save the results file
        """
        # Combine all tasks
        all_tasks = {
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "running": self.running_tasks,
            "summary": self.summarize_results()
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(all_tasks, f, indent=2)
                
            self.logger.info(f"All task results exported to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export task results: {e}")


class MockCoordinator:
    """
    Mock coordinator class for testing the TaskRunner without a full MRCE+ system.
    
    This simulates the behavior of the real coordinator for development and testing.
    """
    
    def __init__(self, success_rate=0.9, min_duration=0.5, max_duration=5.0):
        """
        Initialize mock coordinator.
        
        Args:
            success_rate: Probability of successful task execution (0-1)
            min_duration: Minimum simulated execution time in seconds
            max_duration: Maximum simulated execution time in seconds
        """
        self.success_rate = success_rate
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.logger = logging.getLogger(__name__)
        
    def execute_task(self, task: Dict) -> Dict:
        """
        Simulate task execution.
        
        Args:
            task: Task definition
            
        Returns:
            Simulated task result
            
        Raises:
            Exception: If task "fails" based on success rate
        """
        # Log task received
        self.logger.info(f"Mock coordinator executing task: {task.get('id')} - {task.get('description', 'No description')}")
        
        # Simulate execution time
        duration = self.min_duration + (self.max_duration - self.min_duration) * random.random()
        time.sleep(duration)
        
        # Randomly succeed or fail based on success rate
        import random
        if random.random() > self.success_rate:
            self.logger.warning(f"Mock coordinator simulating failure for task {task.get('id')}")
            raise Exception("Simulated task failure")
            
        # Generate mock result based on task type
        result = self._generate_mock_result(task)
        
        self.logger.info(f"Mock coordinator completed task {task.get('id')} successfully")
        return result
        
    def _generate_mock_result(self, task: Dict) -> Dict:
        """Generate a mock result appropriate for the task type."""
        task_type = task.get("type", "unknown")
        
        base_result = {
            "completion_status": "success",
            "confidence": round(0.7 + 0.3 * random.random(), 2),  # Random confidence between 0.7 and 1.0
            "execution_notes": f"Task executed using mock coordinator with simulated {task_type} processing"
        }
        
        # Add type-specific mock results
        if task_type == "reasoning":
            base_result["solution"] = "Mock reasoning solution with logical steps A→B→C→D"
            base_result["reasoning_path"] = ["Step 1: Identified key variables", "Step 2: Applied constraints", "Step 3: Derived conclusion"]
            
        elif task_type == "creative":
            base_result["creative_output"] = "Mock creative content generated according to specifications"
            base_result["inspiration_sources"] = ["Source 1", "Source 2"]
            
        elif task_type == "research":
            base_result["findings"] = "Mock research findings synthesized from multiple sources"
            base_result["sources"] = ["Source A", "Source B", "Source C"]
            base_result["reliability_assessment"] = "Medium-high confidence in findings based on source quality"
            
        elif task_type == "planning":
            base_result["plan"] = {
                "phases": ["Phase 1", "Phase 2", "Phase 3"],
                "key_milestones": ["Milestone A", "Milestone B"],
                "resource_requirements": {"time": "Est. 3 weeks", "personnel": "2 team members"}
            }
            
        elif task_type == "evaluation":
            base_result["evaluation_results"] = {
                "Option A": {"score": 7.2, "strengths": ["S1", "S2"], "weaknesses": ["W1"]},
                "Option B": {"score": 8.5, "strengths": ["S1", "S2", "S3"], "weaknesses": []}
            }
            base_result["recommendation"] = "Option B is recommended based on evaluation criteria"
            
        elif task_type == "critique":
            base_result["critique"] = {
                "strengths": ["Well-organized structure", "Clear objectives"],
                "weaknesses": ["Insufficient evidence", "Logical inconsistency in section 2"],
                "improvement_suggestions": ["Strengthen evidence base", "Resolve logical inconsistency"]
            }
            
        elif task_type == "classification":
            base_result["classification_results"] = {
                "Item 1": {"category": "Category A", "confidence": 0.92},
                "Item 2": {"category": "Category B", "confidence": 0.87},
                "Item 3": {"category": "Category A", "confidence": 0.64}
            }
            base_result["classification_notes"] = "Item 3 shows characteristics of multiple categories"
            
        elif task_type == "integration":
            base_result["integration_solution"] = {
                "architecture": "Mock integration architecture using pattern X",
                "data_model": "Unified schema with key entities A, B, C",
                "implementation_approach": "Phased implementation with initial focus on core components"
            }
            
        elif task_type == "question_answering":
            base_result["answer"] = "This is a mock comprehensive answer to the question, covering key aspects A, B, and C with supporting evidence."
            base_result["sources"] = ["Reference 1", "Reference 2"]
            base_result["certainty_level"] = "High for main claims, medium for specific details"
            
        else:
            base_result["generic_result"] = "Mock result for unspecified task type"
            
        return base_result
            

# For testing
if __name__ == "__main__":
    import random
    from task_generator import TaskGenerator
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create mock coordinator
    mock_coordinator = MockCoordinator(success_rate=0.9)
    
    # Create task runner
    runner = TaskRunner(coordinator=mock_coordinator)
    
    # Generate some sample tasks
    generator = TaskGenerator()
    tasks = generator.generate_batch(count=5, varied=True)
    
    # Run tasks
    task_ids = runner.run_batch(tasks)
    
    # Print results
    summary = runner.summarize_results()
    print("\nTask Execution Summary:")
    print(f"Total tasks: {summary['total_tasks']}")
    print(f"Completed: {summary['completed']} ({summary['success_rate']:.1f}% success rate)")
    print(f"Failed: {summary['failed']}")
    print(f"Avg execution time: {summary['avg_execution_time']:.2f}s")
    
    # Export results
    runner.export_all_results("task_execution_results.json")
    print("\nResults exported to task_execution_results.json")