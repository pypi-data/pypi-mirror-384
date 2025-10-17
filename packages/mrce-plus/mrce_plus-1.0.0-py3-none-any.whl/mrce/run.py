"""
run.py

Main execution script for the MRCE+ system.

This script handles initialization of all components and provides
command line interfaces for running the system in different modes.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional
import time

# Import core components
from mrce.core.memory import Memory
from mrce.core.inner_loop import InnerLoop
from mrce.core.middle_loop import MiddleLoop
from mrce.core.outer_loop import OuterLoop
from mrce.core.igvam import IGVAM
from mrce.core.agents import MultiAgentCoordinator
from mrce.core.environment import Environment

# Import production components
from mrce.production.security_governance import CausalIntegrityWatchdog, AuditTrail, ComplianceMetrics
from mrce.production.performance_optimization import OptimizedDataFlow, ResourceMonitor, AdaptiveScaler
from mrce.production.production_monitoring import LoggingFramework, MetricsCollector, AlertManager, DistributedTracer, TracerConfig

# Import advanced components
from mrce.advanced.db_memory import DatabaseMemory
from mrce.advanced.distributed_agents import DistributedAgentPool
from mrce.advanced.llm_integration import LLMProvider
from mrce.advanced.hybrid_modules import HybridModuleRegistry
from mrce.advanced.evolutionary_crucible import Crucible

class MRCESystem:
    """
    Main MRCE+ system class.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the MRCE+ system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.logger.info("Initializing MRCE+ system")
        
        # Initialize components based on configuration
        self.memory = self._init_memory()
        self.environment = Environment(config=self.config["environment"])
        self.igvam = IGVAM(config=self.config["igvam"])
        
        # Loops
        self.inner_loop = InnerLoop(self.memory)
        self.middle_loop = MiddleLoop(self.memory)
        self.outer_loop = OuterLoop(self.memory, self.igvam)
        
        # Initialize agents
        self.agents = MultiAgentCoordinator(
            agent_specs=self.config["agents"]["specs"],
            communication=self.config["agents"]["communication"]
        )
        
        # Production components
        self.setup_production_components()
        
        # Advanced components
        self.setup_advanced_components()
        
        self.logger.info("MRCE+ system initialization complete")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict[str, Any]: Configuration
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging.
        
        Returns:
            logging.Logger: Logger
        """
        log_config = self.config["logging"]
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format=log_config["format"],
            filename=log_config.get("file"),
            filemode='a'
        )
        
        logger = logging.getLogger("mrce")
        
        # Add console handler if file logging
        if log_config.get("file"):
            console = logging.StreamHandler()
            console.setLevel(getattr(logging, log_config["level"]))
            formatter = logging.Formatter(log_config["format"])
            console.setFormatter(formatter)
            logger.addHandler(console)
            
        return logger
    
    def _init_memory(self) -> Memory:
        """
        Initialize memory system based on configuration.
        
        Returns:
            Memory: Memory system
        """
        # Basic in-memory
        memory = Memory(vector_dim=self.config["memory"]["vector_dim"])
        
        # Use database if configured
        if self.config["use_persistence"]:
            db_config = self.config["database"]
            self.logger.info(f"Setting up persistent memory with {db_config['type']}")
            # Would connect to database, but just use basic Memory for demo
        
        return memory
    
    def setup_production_components(self) -> None:
        """
        Initialize production components.
        """
        # Monitoring
        if self.config["logging"]["structured"]:
            self.logger.info("Setting up structured logging and monitoring")
            self.logging_framework = LoggingFramework(structured=True)
            self.metrics = MetricsCollector()
            self.alerts = AlertManager(self.metrics)
            
            if self.config["logging"].get("distributed"):
                tracer_config = TracerConfig(
                    service_name="mrce",
                    environment=self.config["mode"],
                    sampling_rate=self.config["monitoring"]["tracing"]["sampling_rate"]
                )
                self.tracer = DistributedTracer(tracer_config)
        
        # Security
        self.logger.info("Setting up security governance")
        self.causal_watchdog = CausalIntegrityWatchdog(self.memory)
        self.audit_trail = AuditTrail(self.config["security"]["audit_path"])
        self.compliance = ComplianceMetrics(self.config["security"]["constraints"])
        
        # Performance
        self.logger.info("Setting up performance optimization")
        self.dataflow = OptimizedDataFlow(
            max_concurrent_ops=self.config["performance"]["max_concurrent_ops"]
        )
        self.resource_monitor = ResourceMonitor(
            thresholds=self.config["performance"]["throttling"]["thresholds"]
        )
        self.scaler = AdaptiveScaler(
            min_workers=self.config["performance"]["min_workers"],
            max_workers=self.config["performance"]["max_workers"]
        )
    
    def setup_advanced_components(self) -> None:
        """
        Initialize advanced components based on configuration.
        """
        # LLM integration
        if self.config["use_llm"]:
            self.logger.info(f"Setting up LLM integration with {self.config['llm']['provider']}")
            self.llm_provider = LLMProvider(
                provider=self.config["llm"]["provider"],
                model=self.config["llm"]["model"],
                embedding_model=self.config["llm"]["embedding_model"]
            )
        
        # Distributed agents
        if self.config["use_distributed"]:
            self.logger.info("Setting up distributed agent infrastructure")
            self.dist_agents = DistributedAgentPool(
                ray_address=self.config["distributed"]["ray_address"],
                num_agents=sum(spec["replicas"] for spec in self.config["agents"]["specs"])
            )
        
        # Hybrid reasoning
        if self.config["use_hybrid_reasoning"]:
            self.logger.info("Setting up hybrid reasoning modules")
            self.hybrid_modules = HybridModuleRegistry()
        
        # Evolutionary systems
        if self.config["use_evolutionary"]:
            self.logger.info("Setting up evolutionary crucible")
            self.crucible = Crucible(
                igvam=self.igvam,
                test_tasks=[{"type": "basic", "difficulty": "medium"}]  # Placeholder
            )
    
    def run(self, task: str) -> Dict[str, Any]:
        """
        Run the MRCE+ system on a task.
        
        Args:
            task: Task to run
            
        Returns:
            Dict[str, Any]: Results
        """
        self.logger.info(f"Running task: {task}")
        
        start_time = time.time()
        
        # Process with agents
        agent_outputs = self.agents.coordinate(task, self.memory)
        
        # Inner loop processing
        inner_output = self.inner_loop.run(task)
        
        # Middle loop reflection (periodic)
        if self.memory.episodic.count() % 5 == 0:  # Every 5 tasks
            self.middle_loop.reflect()
            
        # Outer loop evolution (less frequent)
        if self.memory.episodic.count() % 20 == 0:  # Every 20 tasks
            heuristic = self.outer_loop.evolve()
            alignment = self.igvam.evaluate_heuristic(heuristic)
            self.logger.info(f"Outer loop evolution: {heuristic}, alignment: {alignment}")
            
        # Record audit
        self.audit_trail.record(
            action="process_task",
            subject="system",
            object=task,
            outcome=inner_output
        )
        
        duration = time.time() - start_time
        self.logger.info(f"Task completed in {duration:.2f}s")
        
        return {
            "input": task,
            "output": inner_output,
            "agent_outputs": agent_outputs,
            "duration": duration
        }
    
    def start(self) -> None:
        """
        Start the MRCE+ system services.
        """
        self.logger.info("Starting MRCE+ system services")
        
        # Start monitoring if configured
        if hasattr(self, "metrics"):
            self.metrics.start_collection()
            
        if hasattr(self, "alerts"):
            self.alerts.start()
            
        if hasattr(self, "tracer"):
            self.tracer.start()
            
        if hasattr(self, "resource_monitor"):
            self.resource_monitor.start()
            
        self.logger.info("System ready")
    
    def stop(self) -> None:
        """
        Stop the MRCE+ system services.
        """
        self.logger.info("Stopping MRCE+ system services")
        
        # Stop monitoring if configured
        if hasattr(self, "metrics"):
            self.metrics.stop_collection()
            
        if hasattr(self, "alerts"):
            self.alerts.stop()
            
        if hasattr(self, "tracer"):
            self.tracer.stop()
            
        if hasattr(self, "resource_monitor"):
            self.resource_monitor.stop()
            
        if hasattr(self, "dist_agents"):
            self.dist_agents.shutdown()
            
        self.logger.info("System shutdown complete")

def main():
    """
    Main entry point.
    """
    parser = argparse.ArgumentParser(description="MRCE+ System")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev", help="Operating mode")
    parser.add_argument("--config", default=None, help="Configuration file")
    parser.add_argument("--task", default=None, help="Task to run")
    args = parser.parse_args()
    
    # Determine config file
    if args.config:
        config_path = args.config
    else:
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        config_path = os.path.join(config_dir, f"{args.mode}_config.json")
    
    # Initialize system
    system = MRCESystem(config_path)
    
    # Start services
    system.start()
    
    try:
        if args.task:
            # Run single task
            result = system.run(args.task)
            print(json.dumps(result, indent=2))
        else:
            # Interactive mode
            print("MRCE+ Interactive Mode")
            print("Enter 'exit' to quit")
            
            while True:
                task = input("\nTask: ")
                if task.lower() == "exit":
                    break
                    
                result = system.run(task)
                print(f"Output: {result['output']}")
                print(f"Duration: {result['duration']:.2f}s")
    except KeyboardInterrupt:
        print("\nInterrupted. Shutting down...")
    finally:
        system.stop()

if __name__ == "__main__":
    main()