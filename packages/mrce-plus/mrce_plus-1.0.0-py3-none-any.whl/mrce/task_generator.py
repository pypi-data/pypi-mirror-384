"""
MRCE+ Task Generator

This module provides sample task generation for the MRCE+ system to demonstrate its capabilities.
It creates varied task types with different complexity levels to test and showcase the system.
"""

import json
import random
import uuid
from typing import Dict, List, Any, Optional, Union
import datetime

class TaskGenerator:
    """
    Generates sample tasks for testing and demonstrating the MRCE+ system capabilities.
    
    This class creates different types of tasks with varying complexity and parameters
    to exercise different aspects of the multi-agent reasoning system.
    """
    
    def __init__(
        self, 
        config_path: Optional[str] = None,
        seed: Optional[int] = None
    ):
        """
        Initialize the task generator.
        
        Args:
            config_path: Path to task configuration file (optional)
            seed: Random seed for reproducibility
        """
        # Initialize random seed if provided
        if seed is not None:
            random.seed(seed)
            
        # Load config if provided, otherwise use defaults
        self.config = self._load_config(config_path) if config_path else self._default_config()
        
        # Available task types
        self.task_types = [
            "reasoning",          # Logic puzzles and reasoning tasks
            "creative",           # Creative writing and generation
            "research",           # Information gathering and synthesis
            "planning",           # Multi-step planning problems
            "evaluation",         # Evaluating options or solutions
            "critique",           # Finding issues in existing content
            "classification",     # Categorizing items
            "integration",        # Combining multiple data sources
            "question_answering"  # Direct Q&A tasks
        ]
        
        # For storing generated tasks
        self.generated_tasks = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load task configuration from file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config from {config_path}: {e}")
            return self._default_config()
            
    def _default_config(self) -> Dict:
        """Create default task configuration."""
        return {
            "complexity_weights": {
                "simple": 0.3,
                "moderate": 0.5,
                "complex": 0.2
            },
            "task_type_weights": {
                # Equal weights for all task types by default
            },
            "domains": [
                "general_knowledge",
                "science",
                "business",
                "technology",
                "healthcare",
                "finance",
                "education",
                "environment",
                "social_issues"
            ],
            "task_templates": {
                # These will be populated by task type generators
            }
        }
        
    def generate_task(
        self, 
        task_type: Optional[str] = None, 
        complexity: Optional[str] = None,
        domain: Optional[str] = None
    ) -> Dict:
        """
        Generate a single task with the specified parameters.
        
        Args:
            task_type: Type of task to generate (if None, randomly selected)
            complexity: Complexity level (simple, moderate, complex)
            domain: Domain area for the task content
            
        Returns:
            Task definition dictionary
        """
        # Select task type if not specified
        if task_type is None:
            task_type = self._select_task_type()
            
        # Select complexity if not specified
        if complexity is None:
            complexity = self._select_complexity()
            
        # Select domain if not specified
        if domain is None:
            domain = random.choice(self.config["domains"])
            
        # Generate the task based on type
        if task_type == "reasoning":
            task = self._generate_reasoning_task(complexity, domain)
        elif task_type == "creative":
            task = self._generate_creative_task(complexity, domain)
        elif task_type == "research":
            task = self._generate_research_task(complexity, domain)
        elif task_type == "planning":
            task = self._generate_planning_task(complexity, domain)
        elif task_type == "evaluation":
            task = self._generate_evaluation_task(complexity, domain)
        elif task_type == "critique":
            task = self._generate_critique_task(complexity, domain)
        elif task_type == "classification":
            task = self._generate_classification_task(complexity, domain)
        elif task_type == "integration":
            task = self._generate_integration_task(complexity, domain)
        elif task_type == "question_answering":
            task = self._generate_qa_task(complexity, domain)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
            
        # Add metadata
        task.update({
            "id": str(uuid.uuid4()),
            "type": task_type,
            "complexity": complexity,
            "domain": domain,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "pending"
        })
        
        # Add to generated tasks list
        self.generated_tasks.append(task)
        
        return task
        
    def generate_batch(
        self, 
        count: int = 10, 
        varied: bool = True,
        **kwargs
    ) -> List[Dict]:
        """
        Generate a batch of tasks.
        
        Args:
            count: Number of tasks to generate
            varied: If True, vary task types and complexity
            **kwargs: Parameters to pass to generate_task
            
        Returns:
            List of task dictionaries
        """
        batch = []
        
        for _ in range(count):
            # If varied, don't pass type/complexity to allow random selection
            if varied:
                task = self.generate_task()
            else:
                task = self.generate_task(**kwargs)
                
            batch.append(task)
            
        return batch
        
    def export_tasks(self, filepath: str):
        """
        Export generated tasks to a JSON file.
        
        Args:
            filepath: Path to save the task file
        """
        with open(filepath, 'w') as f:
            json.dump(self.generated_tasks, f, indent=2)
            
    def _select_task_type(self) -> str:
        """Select a task type based on weights or randomly."""
        weights = self.config.get("task_type_weights", {})
        
        if not weights:
            return random.choice(self.task_types)
            
        # Use weights if provided
        types = list(weights.keys())
        weights_list = [weights[t] for t in types]
        
        return random.choices(types, weights=weights_list, k=1)[0]
        
    def _select_complexity(self) -> str:
        """Select complexity level based on weights."""
        weights = self.config.get("complexity_weights", {
            "simple": 0.3,
            "moderate": 0.5,
            "complex": 0.2
        })
        
        levels = list(weights.keys())
        weights_list = [weights[level] for level in levels]
        
        return random.choices(levels, weights=weights_list, k=1)[0]
        
    # Task generator methods
    
    def _generate_reasoning_task(self, complexity: str, domain: str) -> Dict:
        """Generate a reasoning task of specified complexity and domain."""
        
        if complexity == "simple":
            templates = [
                {
                    "description": "Determine which statement logically follows from the given premises.",
                    "content": {
                        "premises": [
                            "All electric cars produce zero direct emissions.",
                            "{car_type} is an electric car."
                        ],
                        "statements": [
                            "{car_type} produces zero direct emissions.",
                            "{car_type} is environmentally friendly.",
                            "{car_type} does not use fossil fuels.",
                            "{car_type} is cheaper to operate than gas cars."
                        ],
                        "variables": {
                            "car_type": ["Tesla Model 3", "Nissan Leaf", "Chevrolet Bolt", "Rivian R1T"]
                        }
                    }
                },
                {
                    "description": "Solve this logical sequence problem.",
                    "content": {
                        "sequence": "{sequence}",
                        "question": "What is the next number in this sequence?",
                        "variables": {
                            "sequence": ["2, 4, 6, 8, ?", "1, 3, 6, 10, 15, ?", "3, 6, 12, 24, ?"]
                        }
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": "Solve this logical puzzle involving multiple constraints.",
                    "content": {
                        "puzzle": (
                            "Five friends (Alex, Bella, Carlos, Diana, and Eduardo) each have a favorite "
                            "color (red, blue, green, yellow, or purple) and a favorite pet "
                            "(dog, cat, bird, fish, or hamster). Based on the following clues, "
                            "determine each person's favorite color and pet.\n\n"
                            "1. The person who likes {color1} also likes {pet1}.\n"
                            "2. {person1} likes {pet2}, but not {color2}.\n"
                            "3. {person2}'s favorite color is {color3}.\n"
                            "4. The person who likes {pet3} doesn't like {color4}.\n"
                            "5. {person3} likes {color5} and {person4} has a {pet4}."
                        ),
                        "variables": {
                            "color1": ["red", "blue", "green"],
                            "pet1": ["dog", "cat", "bird"],
                            "person1": ["Alex", "Bella", "Carlos"],
                            "pet2": ["fish", "hamster", "bird"],
                            "color2": ["yellow", "purple", "green"],
                            "person2": ["Diana", "Eduardo", "Alex"],
                            "color3": ["blue", "purple", "red"],
                            "pet3": ["dog", "cat", "fish"],
                            "color4": ["red", "green", "yellow"],
                            "person3": ["Bella", "Carlos", "Diana"],
                            "color5": ["purple", "yellow", "blue"],
                            "person4": ["Eduardo", "Alex", "Bella"],
                            "pet4": ["hamster", "fish", "dog"]
                        }
                    }
                }
            ]
        else:  # complex
            templates = [
                {
                    "description": "Analyze this complex logical scenario with multiple layers of inference.",
                    "content": {
                        "scenario": (
                            "A software company needs to assign programmers to projects. "
                            "There are 6 programmers (P1-P6) and 4 projects (A-D). "
                            "Each project requires specific expertise in languages: "
                            "Project A needs Python and JavaScript, "
                            "Project B needs Java and C++, "
                            "Project C needs Python and Java, "
                            "Project D needs JavaScript and C++.\n\n"
                            "Each programmer knows the following languages:\n"
                            "- P1: Python, Java\n"
                            "- P2: JavaScript, C++\n"
                            "- P3: Python, JavaScript\n"
                            "- P4: Java, C++\n"
                            "- P5: Python, C++\n"
                            "- P6: Java, JavaScript\n\n"
                            "Additional constraints:\n"
                            "1. Each project needs exactly two programmers.\n"
                            "2. Each programmer can work on at most two projects.\n"
                            "3. P1 and P4 cannot work together.\n"
                            "4. P3 must work on Project A.\n"
                            "5. P2 cannot work on Project B."
                        ),
                        "question": "Determine a valid assignment of programmers to projects that satisfies all constraints."
                    }
                }
            ]
            
        # Select a template and fill in variables
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": self._fill_template_variables(template["content"])
        }
        
        return task
        
    def _generate_creative_task(self, complexity: str, domain: str) -> Dict:
        """Generate a creative task of specified complexity and domain."""
        
        if domain == "general_knowledge":
            topics = ["historical events", "cultural traditions", "famous landmarks", "natural phenomena"]
        elif domain == "science":
            topics = ["astronomy", "biology", "chemistry", "physics", "computer science"]
        elif domain == "technology":
            topics = ["artificial intelligence", "blockchain", "virtual reality", "quantum computing"]
        else:
            topics = ["innovation", "sustainability", "education", "healthcare"]
            
        topic = random.choice(topics)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Write a short story (250 words) about {topic}.",
                    "content": {
                        "format": "short story",
                        "word_count": 250,
                        "topic": topic
                    }
                },
                {
                    "description": f"Create a poem about {topic}.",
                    "content": {
                        "format": "poem",
                        "style": random.choice(["haiku", "sonnet", "free verse"]),
                        "topic": topic
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": f"Write a short story (500 words) that combines {topic} with {random.choice(topics)}.",
                    "content": {
                        "format": "short story",
                        "word_count": 500,
                        "primary_topic": topic,
                        "secondary_topic": random.choice([t for t in topics if t != topic]),
                        "elements_to_include": [
                            random.choice(["surprise ending", "flashback", "dialogue", "metaphor"]),
                            random.choice(["conflict", "resolution", "character development"])
                        ]
                    }
                }
            ]
        else:  # complex
            genres = ["science fiction", "mystery", "fantasy", "historical fiction", "dystopian"]
            characters = ["scientist", "artist", "politician", "teacher", "entrepreneur", "journalist"]
            settings = ["future city", "ancient civilization", "remote island", "space station", "alternate reality"]
            
            templates = [
                {
                    "description": (
                        f"Create an original story (800-1000 words) in the {random.choice(genres)} genre "
                        f"that explores the implications of {topic}."
                    ),
                    "content": {
                        "format": "short story",
                        "word_count": random.randint(800, 1000),
                        "genre": random.choice(genres),
                        "topic": topic,
                        "main_character": random.choice(characters),
                        "setting": random.choice(settings),
                        "elements_to_include": [
                            "character development arc",
                            "symbolic representation of key themes",
                            "thought-provoking conclusion",
                            random.choice(["ethical dilemma", "technological innovation", "social commentary"])
                        ]
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]  # No variable substitution needed here
        }
        
        return task
        
    def _generate_research_task(self, complexity: str, domain: str) -> Dict:
        """Generate a research task of specified complexity and domain."""
        
        # Define topic options based on domain
        if domain == "science":
            topics = ["renewable energy", "genetic engineering", "climate change", "quantum computing", "neuroscience"]
        elif domain == "business":
            topics = ["digital transformation", "sustainable business models", "remote work trends", "global supply chains"]
        elif domain == "technology":
            topics = ["artificial intelligence ethics", "blockchain applications", "edge computing", "IoT security"]
        elif domain == "healthcare":
            topics = ["telemedicine", "precision medicine", "mental health innovations", "healthcare accessibility"]
        else:
            topics = ["emerging technologies", "social impact", "economic trends", "environmental solutions"]
            
        topic = random.choice(topics)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Research and summarize the key concepts of {topic}.",
                    "content": {
                        "topic": topic,
                        "format": "summary",
                        "expected_length": "300-400 words",
                        "focus_areas": [
                            "core concepts",
                            "historical development",
                            "current applications"
                        ]
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": f"Research the impact of {topic} on {random.choice(['industry', 'society', 'policy', 'environment'])} and analyze key trends.",
                    "content": {
                        "primary_topic": topic,
                        "perspective": random.choice(["industry", "society", "policy", "environment"]),
                        "format": "analytical report",
                        "expected_length": "600-800 words",
                        "required_sections": [
                            "executive summary",
                            "current state analysis",
                            "impact assessment",
                            "future trends",
                            "conclusions"
                        ]
                    }
                }
            ]
        else:  # complex
            perspectives = ["technological", "economic", "social", "environmental", "ethical", "political"]
            selected_perspectives = random.sample(perspectives, 3)
            
            templates = [
                {
                    "description": (
                        f"Conduct a comprehensive research analysis on {topic} examining multiple perspectives "
                        f"and synthesizing information from diverse sources."
                    ),
                    "content": {
                        "primary_topic": topic,
                        "perspectives": selected_perspectives,
                        "format": "research paper",
                        "expected_length": "1200-1500 words",
                        "required_elements": [
                            "literature review",
                            "cross-disciplinary analysis",
                            "case studies",
                            "critical evaluation of sources",
                            "synthesis of multiple viewpoints",
                            "identification of knowledge gaps",
                            "recommendations for further research"
                        ]
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _generate_planning_task(self, complexity: str, domain: str) -> Dict:
        """Generate a planning task of specified complexity and domain."""
        
        if domain == "business":
            scenarios = ["product launch", "market expansion", "corporate restructuring", "digital transformation"]
        elif domain == "technology":
            scenarios = ["software development project", "system migration", "cybersecurity implementation", "IT infrastructure upgrade"]
        elif domain == "education":
            scenarios = ["curriculum development", "school improvement plan", "educational technology rollout", "academic research project"]
        else:
            scenarios = ["community event", "personal development plan", "home renovation", "travel itinerary"]
            
        scenario = random.choice(scenarios)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Create a simple plan for a {scenario}.",
                    "content": {
                        "scenario": scenario,
                        "required_elements": [
                            "goals",
                            "timeline",
                            "key tasks",
                            "resource requirements"
                        ],
                        "constraints": [
                            "1-2 month timeframe",
                            "limited budget"
                        ]
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": f"Develop a comprehensive plan for a {scenario} that balances multiple objectives.",
                    "content": {
                        "scenario": scenario,
                        "objectives": [
                            "efficiency",
                            "quality",
                            "cost-effectiveness",
                            random.choice(["sustainability", "innovation", "risk mitigation"])
                        ],
                        "required_elements": [
                            "executive summary",
                            "stakeholder analysis",
                            "phased implementation approach",
                            "timeline with milestones",
                            "resource allocation",
                            "risk assessment",
                            "success metrics"
                        ],
                        "constraints": [
                            "3-6 month timeframe",
                            "defined budget",
                            random.choice(["regulatory requirements", "stakeholder expectations", "technical limitations"])
                        ]
                    }
                }
            ]
        else:  # complex
            challenges = [
                "stakeholder conflicts",
                "resource limitations",
                "technological uncertainty",
                "market volatility",
                "regulatory changes",
                "skill gaps",
                "competitive pressures"
            ]
            selected_challenges = random.sample(challenges, 3)
            
            templates = [
                {
                    "description": (
                        f"Create a strategic, multi-phase plan for a complex {scenario} "
                        f"that addresses multiple constraints and optimization criteria."
                    ),
                    "content": {
                        "scenario": scenario,
                        "strategic_goals": [
                            "long-term sustainability",
                            "competitive advantage",
                            "organizational transformation",
                            "innovation leadership"
                        ],
                        "challenges": selected_challenges,
                        "required_elements": [
                            "strategic analysis (SWOT, PESTEL)",
                            "vision and mission alignment",
                            "scenario planning with contingencies",
                            "resource optimization strategy",
                            "comprehensive risk management framework",
                            "stakeholder engagement plan",
                            "change management approach",
                            "detailed implementation roadmap",
                            "governance structure",
                            "monitoring and evaluation framework"
                        ],
                        "constraints": [
                            "12-18 month timeframe",
                            "cross-functional dependencies",
                            "budgetary limitations",
                            "compliance requirements"
                        ]
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _generate_evaluation_task(self, complexity: str, domain: str) -> Dict:
        """Generate an evaluation task of specified complexity and domain."""
        
        if domain == "business":
            subjects = ["business strategies", "marketing campaigns", "investment opportunities", "organizational structures"]
        elif domain == "technology":
            subjects = ["software tools", "technical architectures", "development methodologies", "technology vendors"]
        elif domain == "education":
            subjects = ["teaching methodologies", "educational resources", "assessment techniques", "curriculum designs"]
        else:
            subjects = ["project proposals", "product designs", "service offerings", "policy options"]
            
        subject = random.choice(subjects)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Evaluate and compare two different {subject}.",
                    "content": {
                        "subject": subject,
                        "options": [f"Option A: {subject.rstrip('s')} 1", f"Option B: {subject.rstrip('s')} 2"],
                        "criteria": [
                            "effectiveness",
                            "cost",
                            "ease of implementation",
                            random.choice(["sustainability", "scalability", "innovation"])
                        ],
                        "format": "comparative analysis",
                        "expected_output": "recommendation with rationale"
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": f"Conduct a multi-criteria evaluation of three {subject} using weighted assessment factors.",
                    "content": {
                        "subject": subject,
                        "options": [
                            f"Option A: {subject.rstrip('s')} 1", 
                            f"Option B: {subject.rstrip('s')} 2", 
                            f"Option C: {subject.rstrip('s')} 3"
                        ],
                        "primary_criteria": [
                            {"name": "effectiveness", "weight": 0.3},
                            {"name": "cost-efficiency", "weight": 0.25},
                            {"name": "implementation complexity", "weight": 0.2},
                            {"name": random.choice(["sustainability", "innovation", "risk"]), "weight": 0.15},
                            {"name": random.choice(["scalability", "user satisfaction", "strategic alignment"]), "weight": 0.1}
                        ],
                        "context": random.choice([
                            "resource-constrained environment", 
                            "rapidly changing market", 
                            "competitive industry",
                            "regulatory environment"
                        ]),
                        "format": "structured analysis with scoring matrix",
                        "expected_output": "ranked recommendations with justifications"
                    }
                }
            ]
        else:  # complex
            stakeholders = ["executive leadership", "operational teams", "customers", "investors", "regulators", "partners"]
            selected_stakeholders = random.sample(stakeholders, 3)
            
            templates = [
                {
                    "description": (
                        f"Perform a comprehensive evaluation of multiple {subject} considering diverse stakeholder perspectives, "
                        f"uncertainty factors, and both short and long-term impacts."
                    ),
                    "content": {
                        "subject": subject,
                        "options": [
                            f"Option A: {subject.rstrip('s')} 1", 
                            f"Option B: {subject.rstrip('s')} 2", 
                            f"Option C: {subject.rstrip('s')} 3",
                            f"Option D: {subject.rstrip('s')} 4"
                        ],
                        "evaluation_framework": {
                            "strategic_dimensions": [
                                "financial viability",
                                "strategic alignment",
                                "operational feasibility",
                                "risk profile",
                                "innovation potential"
                            ],
                            "stakeholder_perspectives": selected_stakeholders,
                            "timeframes": ["short-term (0-1 year)", "medium-term (1-3 years)", "long-term (3+ years)"],
                            "uncertainty_factors": random.sample([
                                "market volatility",
                                "technological change",
                                "regulatory shifts",
                                "competitive dynamics",
                                "resource availability"
                            ], 2)
                        },
                        "analysis_requirements": [
                            "sensitivity analysis",
                            "scenario planning",
                            "risk-adjusted evaluations",
                            "stakeholder impact assessment",
                            "trade-off analysis",
                            "implementation considerations"
                        ],
                        "format": "comprehensive evaluation report",
                        "expected_output": "strategic recommendation with implementation roadmap"
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _generate_critique_task(self, complexity: str, domain: str) -> Dict:
        """Generate a critique task of specified complexity and domain."""
        
        if domain == "technology":
            artifacts = ["software application", "technical architecture", "API design", "user interface", "technical documentation"]
        elif domain == "business":
            artifacts = ["business plan", "marketing strategy", "financial projection", "operational process", "product roadmap"]
        elif domain == "education":
            artifacts = ["lesson plan", "educational resource", "assessment method", "curriculum design", "learning objective"]
        else:
            artifacts = ["project proposal", "written document", "strategic plan", "policy framework", "research methodology"]
            
        artifact = random.choice(artifacts)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Critique the provided {artifact} and identify its key strengths and weaknesses.",
                    "content": {
                        "artifact_type": artifact,
                        "artifact_content": f"[Sample {artifact} content would be provided here]",
                        "critique_focus": [
                            "clarity",
                            "completeness",
                            "consistency",
                            random.choice(["practicality", "innovation", "effectiveness"])
                        ],
                        "format": "structured feedback",
                        "expected_output": "balanced critique with 3-4 strengths and 3-4 areas for improvement"
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": (
                        f"Perform a detailed critique of the provided {artifact}, analyzing its effectiveness "
                        f"against industry best practices and identifying specific improvement opportunities."
                    ),
                    "content": {
                        "artifact_type": artifact,
                        "artifact_content": f"[Sample {artifact} content would be provided here]",
                        "evaluation_dimensions": [
                            "technical soundness",
                            "alignment with objectives",
                            "completeness",
                            "clarity and communication",
                            "practicality and feasibility",
                            random.choice(["innovation", "risk management", "scalability", "maintainability"])
                        ],
                        "industry_context": random.choice([
                            "fast-moving technology sector",
                            "highly regulated industry",
                            "competitive consumer market",
                            "resource-constrained environment"
                        ]),
                        "format": "comprehensive analysis",
                        "expected_output": "detailed critique with specific recommendations for improvement"
                    }
                }
            ]
        else:  # complex
            perspectives = [
                "technical feasibility",
                "business value",
                "user experience",
                "operational efficiency",
                "strategic alignment",
                "risk profile",
                "innovation potential",
                "ethical considerations"
            ]
            selected_perspectives = random.sample(perspectives, 4)
            
            templates = [
                {
                    "description": (
                        f"Conduct a multi-dimensional critical analysis of the provided {artifact}, "
                        f"examining it from multiple stakeholder perspectives and considering both "
                        f"immediate implementation factors and long-term strategic implications."
                    ),
                    "content": {
                        "artifact_type": artifact,
                        "artifact_content": f"[Sample {artifact} content would be provided here]",
                        "critique_framework": {
                            "primary_perspectives": selected_perspectives,
                            "stakeholder_considerations": random.sample([
                                "end users",
                                "technical implementers",
                                "business stakeholders",
                                "regulatory compliance",
                                "external partners"
                            ], 3),
                            "temporal_dimensions": ["immediate implementation", "short-term operations", "long-term evolution"]
                        },
                        "contextual_factors": [
                            "industry trends",
                            "organizational constraints",
                            "competitive landscape",
                            "technological evolution"
                        ],
                        "analysis_requirements": [
                            "root cause identification",
                            "impact assessment",
                            "alternative approaches",
                            "implementation considerations",
                            "risk-benefit analysis"
                        ],
                        "format": "comprehensive critique report",
                        "expected_output": "detailed analysis with prioritized recommendations and implementation roadmap"
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _generate_classification_task(self, complexity: str, domain: str) -> Dict:
        """Generate a classification task of specified complexity and domain."""
        
        # Define classification scenarios based on domain
        if domain == "business":
            scenarios = [
                {"name": "customer segmentation", "classes": ["high-value", "medium-value", "low-value"]},
                {"name": "market opportunities", "classes": ["high-priority", "medium-priority", "low-priority"]},
                {"name": "business expenses", "classes": ["essential", "operational", "strategic", "discretionary"]}
            ]
        elif domain == "technology":
            scenarios = [
                {"name": "software bugs", "classes": ["critical", "major", "minor", "cosmetic"]},
                {"name": "feature requests", "classes": ["must-have", "should-have", "nice-to-have", "won't-have"]},
                {"name": "technology investments", "classes": ["core", "adjacent", "transformational"]}
            ]
        elif domain == "healthcare":
            scenarios = [
                {"name": "patient risk levels", "classes": ["high", "moderate", "low"]},
                {"name": "treatment options", "classes": ["first-line", "second-line", "alternative", "experimental"]},
                {"name": "healthcare innovations", "classes": ["preventive", "diagnostic", "therapeutic", "rehabilitative"]}
            ]
        else:
            scenarios = [
                {"name": "content categories", "classes": ["informational", "educational", "promotional", "entertainment"]},
                {"name": "project priorities", "classes": ["urgent", "important", "routine", "backlog"]},
                {"name": "research findings", "classes": ["confirmed", "preliminary", "inconclusive", "contradictory"]}
            ]
            
        scenario = random.choice(scenarios)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Classify the following items into {scenario['name']} categories.",
                    "content": {
                        "classification_type": scenario["name"],
                        "categories": scenario["classes"],
                        "items_to_classify": [f"Item {i+1}" for i in range(10)],
                        "criteria_description": f"Brief explanation of criteria for {scenario['name']} classification",
                        "expected_output": "categorized items with brief justification for each"
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": (
                        f"Develop and apply a structured classification framework for {scenario['name']}, "
                        f"using multiple criteria to categorize items."
                    ),
                    "content": {
                        "classification_type": scenario["name"],
                        "primary_categories": scenario["classes"],
                        "items_to_classify": [f"Item {i+1}" for i in range(15)],
                        "classification_criteria": [
                            "primary characteristic",
                            "secondary characteristic",
                            "contextual factors",
                            random.choice(["impact level", "resource requirements", "time sensitivity"])
                        ],
                        "classification_challenges": random.sample([
                            "ambiguous cases",
                            "overlapping categories",
                            "incomplete information",
                            "evolving conditions"
                        ], 2),
                        "expected_output": "comprehensive classification with decision rationale and handling of edge cases"
                    }
                }
            ]
        else:  # complex
            templates = [
                {
                    "description": (
                        f"Create and apply a multi-dimensional classification system for {scenario['name']} "
                        f"that incorporates hierarchical categories, cross-cutting dimensions, "
                        f"and handles ambiguous or evolving cases."
                    ),
                    "content": {
                        "classification_type": scenario["name"],
                        "primary_categories": scenario["classes"],
                        "secondary_dimensions": random.sample([
                            "urgency",
                            "impact",
                            "resource intensity",
                            "certainty level",
                            "stakeholder alignment"
                        ], 3),
                        "items_to_classify": [f"Item {i+1}" for i in range(20)],
                        "classification_framework": {
                            "hierarchical_structure": "primary categories with subcategories",
                            "cross-cutting_dimensions": "items may have attributes across multiple dimensions",
                            "classification_rules": "explicit decision criteria for category assignment",
                            "exception_handling": "process for addressing edge cases and ambiguities"
                        },
                        "contextual_considerations": [
                            "temporal dynamics (how classification may change over time)",
                            "confidence levels in classifications",
                            "interrelationships between classified items"
                        ],
                        "expected_output": (
                            "comprehensive classification with multi-dimensional analysis, "
                            "visualization of classification patterns, and system for handling evolving classifications"
                        )
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _generate_integration_task(self, complexity: str, domain: str) -> Dict:
        """Generate an integration task of specified complexity and domain."""
        
        if domain == "technology":
            scenarios = [
                {"name": "data integration", "sources": ["customer database", "sales records", "marketing analytics"]},
                {"name": "system integration", "sources": ["legacy system", "cloud service", "mobile application"]},
                {"name": "API integration", "sources": ["internal API", "partner API", "third-party service"]}
            ]
        elif domain == "business":
            scenarios = [
                {"name": "business process integration", "sources": ["sales process", "fulfillment process", "customer support"]},
                {"name": "post-merger integration", "sources": ["company A systems", "company B processes", "unified reporting"]},
                {"name": "supply chain integration", "sources": ["supplier data", "logistics information", "inventory systems"]}
            ]
        elif domain == "healthcare":
            scenarios = [
                {"name": "healthcare data integration", "sources": ["patient records", "lab results", "treatment protocols"]},
                {"name": "care coordination", "sources": ["primary care", "specialist treatment", "rehabilitation services"]},
                {"name": "health information exchange", "sources": ["hospital system", "clinic records", "pharmacy data"]}
            ]
        else:
            scenarios = [
                {"name": "knowledge integration", "sources": ["research findings", "expert opinions", "case studies"]},
                {"name": "cross-functional integration", "sources": ["department A data", "team B insights", "external benchmarks"]},
                {"name": "multi-source analysis", "sources": ["quantitative data", "qualitative feedback", "contextual information"]}
            ]
            
        scenario = random.choice(scenarios)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Create a basic {scenario['name']} solution combining information from multiple sources.",
                    "content": {
                        "integration_type": scenario["name"],
                        "data_sources": scenario["sources"],
                        "integration_goals": [
                            "create unified view",
                            "ensure consistency",
                            random.choice(["enable reporting", "support decision-making", "improve efficiency"])
                        ],
                        "key_challenges": [
                            "different data formats",
                            random.choice(["access limitations", "update frequencies", "quality variations"])
                        ],
                        "expected_output": "integration approach with combined data structure"
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": (
                        f"Design a comprehensive {scenario['name']} solution that addresses multiple "
                        f"technical and organizational challenges."
                    ),
                    "content": {
                        "integration_type": scenario["name"],
                        "primary_sources": scenario["sources"],
                        "additional_sources": [f"supplementary source {i+1}" for i in range(2)],
                        "integration_objectives": [
                            "create single source of truth",
                            "enable real-time data access",
                            "support advanced analytics",
                            random.choice(["ensure regulatory compliance", "improve operational efficiency"])
                        ],
                        "key_challenges": random.sample([
                            "data quality inconsistencies",
                            "different update frequencies",
                            "semantic differences",
                            "security requirements",
                            "performance constraints",
                            "organizational silos"
                        ], 4),
                        "integration_patterns": random.sample([
                            "extract-transform-load",
                            "real-time streaming",
                            "service-oriented architecture",
                            "data virtualization"
                        ], 2),
                        "expected_output": "detailed integration design with architecture diagram and implementation approach"
                    }
                }
            ]
        else:  # complex
            templates = [
                {
                    "description": (
                        f"Create an enterprise-level {scenario['name']} strategy and implementation plan "
                        f"that addresses complex heterogeneous environments, evolving requirements, "
                        f"and maintains operational continuity."
                    ),
                    "content": {
                        "integration_type": scenario["name"],
                        "integration_scope": {
                            "primary_systems": scenario["sources"],
                            "secondary_systems": [f"secondary system {i+1}" for i in range(3)],
                            "external_integrations": [f"external integration {i+1}" for i in range(2)],
                            "future_considerations": [f"future system {i+1}" for i in range(2)]
                        },
                        "strategic_objectives": [
                            "enterprise data unification",
                            "business process optimization",
                            "analytics and intelligence capabilities",
                            "scalability and future-readiness",
                            random.choice(["regulatory compliance", "customer experience enhancement"])
                        ],
                        "integration_challenges": {
                            "technical": random.sample([
                                "legacy system constraints",
                                "data quality and governance",
                                "real-time vs. batch processing requirements",
                                "security and compliance",
                                "performance at scale"
                            ], 3),
                            "organizational": random.sample([
                                "cross-functional alignment",
                                "change management",
                                "skill gaps",
                                "governance model"
                            ], 2),
                            "operational": random.sample([
                                "minimal disruption requirements",
                                "phased implementation needs",
                                "fallback strategies",
                                "monitoring and support"
                            ], 2)
                        },
                        "architectural_approach": {
                            "integration_patterns": random.sample([
                                "API-first architecture",
                                "event-driven integration",
                                "data lake/warehouse architecture",
                                "microservices approach",
                                "hybrid integration platform"
                            ], 3),
                            "governance_framework": "centralized governance with distributed implementation",
                            "technology_stack": "specified integration technologies and standards"
                        },
                        "implementation_strategy": {
                            "phased_approach": "prioritized integration roadmap",
                            "risk_mitigation": "strategies for addressing key integration risks",
                            "change_management": "process for managing organizational impacts",
                            "monitoring_and_optimization": "continuous improvement framework"
                        },
                        "expected_output": (
                            "comprehensive integration strategy with architectural blueprint, "
                            "detailed implementation roadmap, governance framework, and risk mitigation strategies"
                        )
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _generate_qa_task(self, complexity: str, domain: str) -> Dict:
        """Generate a question-answering task of specified complexity and domain."""
        
        # Define question types based on domain
        if domain == "general_knowledge":
            questions = [
                "What are the key factors that contributed to the Industrial Revolution?",
                "How do different cultural perspectives influence global business practices?",
                "What are the major theories explaining the extinction of dinosaurs?"
            ]
        elif domain == "science":
            questions = [
                "How do quantum computers differ from classical computers?",
                "What are the primary mechanisms of climate change?",
                "How does CRISPR-Cas9 gene editing technology work?"
            ]
        elif domain == "business":
            questions = [
                "What factors contribute to successful digital transformation in organizations?",
                "How do different leadership styles impact team performance?",
                "What are the key considerations for expanding a business internationally?"
            ]
        elif domain == "technology":
            questions = [
                "What are the ethical implications of artificial intelligence in decision-making?",
                "How does blockchain technology ensure security and transparency?",
                "What are the tradeoffs between edge computing and cloud computing?"
            ]
        else:
            questions = [
                "What are the key challenges facing sustainable development?",
                "How do social media platforms influence public discourse?",
                "What factors contribute to effective learning environments?"
            ]
            
        question = random.choice(questions)
        
        if complexity == "simple":
            templates = [
                {
                    "description": f"Answer the following question concisely: {question}",
                    "content": {
                        "question": question,
                        "answer_constraints": {
                            "length": "concise (100-200 words)",
                            "focus": "key concepts and main ideas",
                            "structure": "straightforward response"
                        }
                    }
                }
            ]
        elif complexity == "moderate":
            templates = [
                {
                    "description": (
                        f"Provide a detailed answer to the following question, considering multiple perspectives: "
                        f"{question}"
                    ),
                    "content": {
                        "question": question,
                        "answer_requirements": {
                            "depth": "detailed explanation of key concepts",
                            "perspectives": random.sample([
                                "historical context",
                                "current understanding",
                                "theoretical frameworks",
                                "practical applications",
                                "different viewpoints"
                            ], 3),
                            "evidence": "include supporting facts and examples",
                            "structure": "organized with clear sections"
                        },
                        "expected_length": "400-600 words"
                    }
                }
            ]
        else:  # complex
            templates = [
                {
                    "description": (
                        f"Provide a comprehensive analysis in response to this question, synthesizing multiple "
                        f"perspectives and addressing nuances and implications: {question}"
                    ),
                    "content": {
                        "question": question,
                        "analysis_requirements": {
                            "conceptual_depth": "thorough exploration of underlying concepts and principles",
                            "multiple_dimensions": random.sample([
                                "historical evolution",
                                "theoretical frameworks",
                                "practical applications",
                                "ethical considerations",
                                "societal implications",
                                "future directions",
                                "contrasting viewpoints"
                            ], 4),
                            "critical_analysis": "evaluation of strengths and limitations of different approaches",
                            "synthesis": "integration of ideas across perspectives",
                            "contextualization": "placement within broader context and relevance"
                        },
                        "structural_requirements": {
                            "framework": "logical progression with clear sections",
                            "evidence": "integration of supporting evidence and examples",
                            "counterarguments": "consideration of alternative viewpoints",
                            "implications": "discussion of broader significance and applications"
                        },
                        "expected_length": "800-1000 words"
                    }
                }
            ]
            
        template = random.choice(templates)
        task = {
            "description": template["description"],
            "content": template["content"]
        }
        
        return task
        
    def _fill_template_variables(self, template_content: Dict) -> Dict:
        """Fill in template variables with randomly selected values."""
        content = template_content.copy()
        
        # Check if there are variables to fill
        if "variables" not in content:
            return content
            
        variables = content.pop("variables")
        
        # Fill all template strings in content with random variable selections
        content = self._replace_variables_recursive(content, variables)
        
        return content
        
    def _replace_variables_recursive(self, obj: Any, variables: Dict) -> Any:
        """Recursively replace variables in strings within nested dictionaries and lists."""
        if isinstance(obj, str):
            # Replace all variables in the string
            result = obj
            for var_name, var_values in variables.items():
                var_pattern = "{" + var_name + "}"
                if var_pattern in result:
                    result = result.replace(var_pattern, random.choice(var_values))
            return result
        elif isinstance(obj, list):
            return [self._replace_variables_recursive(item, variables) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._replace_variables_recursive(v, variables) for k, v in obj.items()}
        else:
            return obj
            
    def get_generator_for_type(self, task_type: str):
        """Get the appropriate generator method for a task type."""
        generators = {
            "reasoning": self._generate_reasoning_task,
            "creative": self._generate_creative_task,
            "research": self._generate_research_task,
            "planning": self._generate_planning_task,
            "evaluation": self._generate_evaluation_task,
            "critique": self._generate_critique_task,
            "classification": self._generate_classification_task,
            "integration": self._generate_integration_task,
            "question_answering": self._generate_qa_task
        }
        
        return generators.get(task_type)
        
# Example usage:
# generator = TaskGenerator()
# simple_task = generator.generate_task(task_type="reasoning", complexity="simple")
# varied_batch = generator.generate_batch(count=5, varied=True)
# generator.export_tasks("sample_tasks.json")