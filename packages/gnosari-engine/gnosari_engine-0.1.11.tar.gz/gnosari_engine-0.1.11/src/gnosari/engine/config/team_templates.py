"""
Team template generator for creating modular team structures.

This module provides functionality to generate modular team configurations
from predefined templates.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MultilineString(str):
    """Custom string class to mark multiline instructions for YAML formatting."""
    pass


def multiline_presenter(dumper, data):
    """Custom YAML presenter for multiline strings."""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')


# Register the custom presenter
yaml.add_representer(MultilineString, multiline_presenter)


class TeamTemplateGenerator:
    """Generates modular team configurations from templates."""
    
    def __init__(self):
        self.templates = {
            "basic": self._basic_template,
            "support": self._support_template,
            "research": self._research_template
        }
    
    async def create_team_from_template(self, team_name: str, template_name: str, output_dir: Path) -> Path:
        """Create a new modular team from a template."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found. Available: {list(self.templates.keys())}")
        
        # Create team directory
        team_dir = output_dir / self._sanitize_name(team_name)
        team_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate template configuration
        template_config = self.templates[template_name](team_name)
        
        # Create directory structure
        await self._create_directory_structure(team_dir)
        
        # Write template files
        await self._write_template_files(team_dir, template_config)
        
        logger.info(f"Created modular team '{team_name}' from template '{template_name}' at {team_dir}")
        return team_dir
    
    async def _create_directory_structure(self, team_dir: Path):
        """Create the modular directory structure."""
        directories = ["agents", "tools", "knowledge", "prompts", "traits"]
        for dir_name in directories:
            (team_dir / dir_name).mkdir(exist_ok=True)
    
    async def _write_template_files(self, team_dir: Path, template_config: Dict[str, Any]):
        """Write template files to the team directory."""
        # Write main configuration
        main_file = team_dir / "main.yaml"
        with open(main_file, 'w', encoding='utf-8') as f:
            yaml.dump(template_config["main"], f, default_flow_style=False, sort_keys=False, indent=2, width=120, allow_unicode=True)
        
        # Write component files
        for component_type, components in template_config.items():
            if component_type == "main":
                continue
                
            component_dir = team_dir / component_type
            for component_id, component_data in components.items():
                component_file = component_dir / f"{component_id}.yaml"
                with open(component_file, 'w', encoding='utf-8') as f:
                    yaml.dump(component_data, f, default_flow_style=False, sort_keys=False, indent=2, width=120, allow_unicode=True)
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize team name for directory usage."""
        import re
        sanitized = re.sub(r'[^\w\-_]', '-', name.lower())
        sanitized = re.sub(r'-+', '-', sanitized)
        return sanitized.strip('-')
    
    def _basic_template(self, team_name: str) -> Dict[str, Any]:
        """Generate basic team template."""
        # Create user-friendly name from team name
        friendly_name = team_name.replace('-', ' ').replace('_', ' ').title()
        
        return {
            "main": {
                "id": self._sanitize_name(team_name),
                "name": friendly_name,
                "description": f"A basic AI team for {friendly_name}",
                "version": "1.0.0",
                "tags": ["basic", "starter"],
                "config": {
                    "max_turns": 50,
                    "timeout": 300
                },
                "overrides": {},
                "components": {}
            },
            "agents": {
                "assistant": {
                    "name": "AI Assistant",
                    "description": "A helpful AI assistant that provides clear and accurate responses",
                    "instructions": MultilineString("You are a helpful AI assistant. Provide clear, accurate, and helpful\nresponses to user queries."),
                    "model": "gpt-4o",
                    "temperature": 0.7,
                    "reasoning_effort": "medium",
                    "orchestrator": True,
                    "tools": ["api_tool"],
                    "knowledge": [],
                    "traits": ["helpful"]
                }
            },
            "tools": {
                "api_tool": {
                    "name": "API Request Tool",
                    "description": "Makes HTTP requests to external APIs and web services",
                    "module": "gnosari.tools.builtin.api_request",
                    "class": "APIRequestTool",
                    "args": {
                        "timeout": 30,
                        "base_headers": {
                            "User-Agent": "Gnosari-Team/1.0"
                        }
                    }
                }
            },
            "knowledge": {},
            "prompts": {},
            "traits": {
                "helpful": {
                    "name": "helpful",
                    "description": "Always tries to be helpful and constructive",
                    "instructions": MultilineString("Focus on providing useful information and actionable advice.\nBe proactive in offering assistance and solutions."),
                    "weight": 1.0,
                    "category": "personality",
                    "tags": ["basic", "supportive"]
                }
            }
        }
    
    def _support_template(self, team_name: str) -> Dict[str, Any]:
        """Generate customer support team template."""
        # Create user-friendly name from team name
        friendly_name = team_name.replace('-', ' ').replace('_', ' ').title()
        
        return {
            "main": {
                "id": self._sanitize_name(team_name),
                "name": friendly_name,
                "description": f"Customer support team for {friendly_name}",
                "version": "1.0.0",
                "tags": ["support", "customer-service"],
                "config": {
                    "max_turns": 100,
                    "timeout": 600
                },
                "overrides": {
                    "agents": {
                        "manager": {
                            "model": "gpt-4o",
                            "temperature": 0.1
                        }
                    }
                },
                "components": {}
            },
            "agents": {
                "manager": {
                    "name": "Support Manager",
                    "description": "Customer support manager who analyzes requests and delegates to specialists",
                    "instructions": MultilineString("You are a customer support manager. Analyze incoming requests and delegate to\nappropriate specialists. Maintain professional communication and ensure customer\nsatisfaction."),
                    "model": "gpt-4o",
                    "temperature": 0.3,
                    "reasoning_effort": "high",
                    "orchestrator": True,
                    "tools": ["api_tool", "file_ops"],
                    "knowledge": ["support_docs"],
                    "traits": ["professional", "decisive"],
                    "delegation": [
                        {
                            "agent": "technical_support",
                            "instructions": "Use for technical issues, bugs, and product functionality questions"
                        },
                        {
                            "agent": "billing_support", 
                            "instructions": "Use for billing, payments, and account management questions"
                        }
                    ]
                },
                "technical_support": {
                    "name": "Technical Support Specialist",
                    "description": "Expert technical support specialist for troubleshooting and product functionality",
                    "instructions": MultilineString("You are a technical support specialist. Handle technical issues, troubleshooting,\nand product functionality questions with expertise and patience."),
                    "model": "gpt-4o",
                    "temperature": 0.2,
                    "reasoning_effort": "high",
                    "orchestrator": False,
                    "tools": ["api_tool", "file_ops"],
                    "knowledge": ["support_docs", "technical_docs"],
                    "traits": ["technical_expert", "patient"]
                },
                "billing_support": {
                    "name": "Billing Support Specialist",
                    "description": "Billing and payment specialist for account management and financial inquiries",
                    "instructions": MultilineString("You are a billing support specialist. Handle payment issues, subscription\nmanagement, and account-related questions with accuracy and empathy."),
                    "model": "gpt-4o",
                    "temperature": 0.1,
                    "reasoning_effort": "medium",
                    "orchestrator": False,
                    "tools": ["api_tool"],
                    "knowledge": ["support_docs"],
                    "traits": ["detail_oriented", "empathetic"]
                }
            },
            "tools": {
                "api_tool": {
                    "name": "API Request Tool",
                    "description": "Makes HTTP requests to external APIs and web services for support operations",
                    "module": "gnosari.tools.builtin.api_request",
                    "class": "APIRequestTool",
                    "args": {
                        "timeout": 30,
                        "base_headers": {
                            "User-Agent": "Gnosari-Support/1.0"
                        }
                    }
                },
                "file_ops": {
                    "name": "File Operations Tool",
                    "description": "Manages support files, logs, and documentation with secure file operations",
                    "module": "gnosari.tools.builtin.file_operations",
                    "class": "FileOperationsTool",
                    "args": {
                        "base_directory": "./support_files",
                        "allowed_extensions": [".txt", ".json", ".md", ".log"],
                        "max_file_size": 1048576
                    }
                }
            },
            "knowledge": {
                "support_docs": {
                    "type": "website",
                    "data": [
                        "https://docs.company.com/support",
                        "https://help.company.com"
                    ],
                    "config": {
                        "llm": {
                            "provider": "openai",
                            "config": {
                                "model": "gpt-4o",
                                "temperature": 0.1
                            }
                        },
                        "chunker": {
                            "chunk_size": 1000,
                            "chunk_overlap": 200
                        }
                    }
                },
                "technical_docs": {
                    "type": "website", 
                    "data": [
                        "https://docs.company.com/api",
                        "https://docs.company.com/troubleshooting"
                    ],
                    "config": {
                        "llm": {
                            "provider": "openai",
                            "config": {
                                "model": "gpt-4o",
                                "temperature": 0.1
                            }
                        },
                        "chunker": {
                            "chunk_size": 1500,
                            "chunk_overlap": 300
                        }
                    }
                }
            },
            "prompts": {},
            "traits": {
                "professional": {
                    "name": "professional",
                    "description": "Maintains professional demeanor in all interactions",
                    "instructions": MultilineString("Use formal language and structured responses while being helpful.\nMaintain professional tone throughout all interactions."),
                    "weight": 1.0,
                    "category": "communication",
                    "tags": ["formal", "business"]
                },
                "decisive": {
                    "name": "decisive",
                    "description": "Makes clear decisions and provides direct guidance",
                    "instructions": MultilineString("Provide clear direction and avoid ambiguous responses.\nMake decisive recommendations when needed."),
                    "weight": 1.2,
                    "category": "workflow",
                    "tags": ["leadership", "clarity"]
                },
                "technical_expert": {
                    "name": "technical_expert",
                    "description": "Deep technical knowledge and problem-solving skills",
                    "instructions": MultilineString("Provide detailed technical explanations and step-by-step solutions.\nUse technical expertise to solve complex problems."),
                    "weight": 1.3,
                    "category": "expertise",
                    "tags": ["technical", "problem-solving"]
                },
                "patient": {
                    "name": "patient",
                    "description": "Patient and understanding with users of all technical levels",
                    "instructions": MultilineString("Explain technical concepts clearly and ask clarifying questions.\nRemain patient even with repetitive questions."),
                    "weight": 1.0,
                    "category": "personality",
                    "tags": ["understanding", "supportive"]
                },
                "detail_oriented": {
                    "name": "detail_oriented",
                    "description": "Extremely careful with financial and account details",
                    "instructions": MultilineString("Double-check all account information and calculations.\nPay careful attention to billing details and accuracy."),
                    "weight": 1.4,
                    "category": "workflow",
                    "tags": ["accuracy", "careful"]
                },
                "empathetic": {
                    "name": "empathetic",
                    "description": "Understanding and empathetic with billing concerns",
                    "instructions": MultilineString("Show understanding for billing frustrations and work toward solutions.\nValidate customer concerns while providing helpful guidance."),
                    "weight": 1.1,
                    "category": "personality",
                    "tags": ["understanding", "supportive"]
                }
            }
        }
    
    def _research_template(self, team_name: str) -> Dict[str, Any]:
        """Generate research team template."""
        # Create user-friendly name from team name
        friendly_name = team_name.replace('-', ' ').replace('_', ' ').title()
        
        return {
            "main": {
                "id": self._sanitize_name(team_name),
                "name": friendly_name,
                "description": f"Research and analysis team for {friendly_name}",
                "version": "1.0.0",
                "tags": ["research", "analysis"],
                "config": {
                    "max_turns": 200,
                    "timeout": 900
                },
                "overrides": {
                    "agents": {
                        "coordinator": {
                            "temperature": 0.2
                        },
                        "analyst": {
                            "reasoning_effort": "high"
                        }
                    }
                },
                "components": {}
            },
            "agents": {
                "coordinator": {
                    "name": "Research Coordinator",
                    "description": "Research coordinator who plans tasks, delegates to specialists, and synthesizes findings",
                    "instructions": MultilineString("You are a research coordinator. Plan research tasks, delegate to specialists,\nand synthesize findings into comprehensive reports."),
                    "model": "gpt-4o",
                    "temperature": 0.3,
                    "reasoning_effort": "high",
                    "orchestrator": True,
                    "tools": ["web_search", "api_tool", "file_ops"],
                    "knowledge": ["research_kb"],
                    "traits": [
                        {
                            "name": "analytical",
                            "description": "Strong analytical and strategic thinking abilities",
                            "instructions": MultilineString("Break down complex research questions into manageable components.\nApply strategic thinking to research planning."),
                            "weight": 1.3
                        },
                        {
                            "name": "thorough",
                            "description": "Ensures comprehensive coverage of research topics",
                            "instructions": MultilineString("Consider multiple perspectives and verify information from multiple sources.\nEnsure comprehensive coverage of all research aspects."),
                            "weight": 1.2
                        }
                    ],
                    "delegation": [
                        {
                            "agent": "analyst",
                            "instructions": "Use for detailed data analysis and statistical research"
                        },
                        {
                            "agent": "writer",
                            "instructions": "Use for synthesizing findings into reports and documentation"
                        }
                    ]
                },
                "analyst": {
                    "name": "Research Analyst",
                    "description": "Expert research analyst for detailed data analysis and evidence-based insights",
                    "instructions": MultilineString("You are a research analyst. Conduct detailed analysis, gather data,\nand provide evidence-based insights on specific research topics."),
                    "model": "gpt-4o",
                    "temperature": 0.2,
                    "reasoning_effort": "high",
                    "orchestrator": False,
                    "tools": ["web_search", "api_tool", "file_ops"],
                    "knowledge": ["research_kb"],
                    "traits": [
                        {
                            "name": "methodical",
                            "description": "Systematic and methodical approach to research",
                            "instructions": MultilineString("Follow structured research methodologies and document all sources.\nMaintain systematic approach to all research tasks."),
                            "weight": 1.4
                        },
                        {
                            "name": "critical_thinker",
                            "description": "Excellent critical thinking and evaluation skills",
                            "instructions": MultilineString("Question assumptions and evaluate source credibility carefully.\nApply critical thinking to all information sources."),
                            "weight": 1.3
                        }
                    ]
                },
                "writer": {
                    "name": "Research Writer",
                    "description": "Professional research writer who transforms findings into clear, structured reports",
                    "instructions": MultilineString("You are a research writer. Transform research findings into clear,\nwell-structured reports and documentation that effectively communicate insights."),
                    "model": "gpt-4o",
                    "temperature": 0.4,
                    "reasoning_effort": "medium",
                    "orchestrator": False,
                    "tools": ["file_ops"],
                    "knowledge": ["research_kb"],
                    "traits": [
                        {
                            "name": "articulate",
                            "description": "Excellent written communication and synthesis skills",
                            "instructions": MultilineString("Create clear, engaging, and well-structured written content.\nSynthesize complex information into accessible formats."),
                            "weight": 1.3
                        },
                        {
                            "name": "detail_oriented",
                            "description": "Careful attention to accuracy and detail in writing",
                            "instructions": MultilineString("Ensure accuracy, proper citations, and clear explanations.\nMaintain high standards for written output quality."),
                            "weight": 1.1
                        }
                    ]
                }
            },
            "tools": {
                "web_search": {
                    "name": "Web Search Tool",
                    "description": "Searches the web for information and research sources",
                    "module": "gnosari.tools.builtin.web_search",
                    "class": "WebSearchTool",
                    "args": {
                        "max_results": 10,
                        "timeout": 30
                    }
                },
                "api_tool": {
                    "name": "API Request Tool",
                    "description": "Makes HTTP requests to external APIs and research databases",
                    "module": "gnosari.tools.builtin.api_request",
                    "class": "APIRequestTool",
                    "args": {
                        "timeout": 60,
                        "base_headers": {
                            "User-Agent": "Gnosari-Research/1.0"
                        }
                    }
                },
                "file_ops": {
                    "name": "File Operations Tool",
                    "description": "Manages research files, reports, and data with support for multiple formats",
                    "module": "gnosari.tools.builtin.file_operations",
                    "class": "FileOperationsTool",
                    "args": {
                        "base_directory": "./research_files",
                        "allowed_extensions": [".txt", ".md", ".json", ".csv", ".pdf"],
                        "max_file_size": 10485760
                    }
                }
            },
            "knowledge": {
                "research_kb": {
                    "type": "directory",
                    "data": [
                        "./research_data",
                        "./references"
                    ],
                    "config": {
                        "llm": {
                            "provider": "openai",
                            "config": {
                                "model": "gpt-4o",
                                "temperature": 0.1
                            }
                        },
                        "chunker": {
                            "chunk_size": 2000,
                            "chunk_overlap": 400
                        }
                    }
                }
            },
            "prompts": {}
        }