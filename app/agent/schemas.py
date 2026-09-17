# app/agent/schemas.py

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs_semantic",
            "description": "Searches for job listings using semantic vector similarity. Use this when the user asks for roles involving specific technologies (e.g. 'backend infra', 'Go', 'Kubernetes', 'FastAPI') or asks for job recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, skills, or job title to match against"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of job listings to return (default 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_skills",
            "description": "Calculates the most frequently required skills across all available job listings. Use this when the user asks what skills are in high demand or what they should learn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top skills to return (default 5)",
                        "default": 5
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_job_by_id",
            "description": "Retrieves comprehensive details about a specific job listing using its numeric ID. Use this when the user asks for more details, stipend, or application link for a specific job.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "The numeric ID of the job listing"
                    }
                },
                "required": ["job_id"]
            }
        }
    }
]

# Append inside AGENT_TOOLS in app/agent/schemas.py:
{
    "type": "function",
    "function": {
        "name": "filter_jobs_parametric",
        "description": "Filters job listings by specific category (e.g. 'Software Engineering (SDE)', 'Quantitative & HFT', 'AI & Machine Learning', 'Backend & Cloud Systems') and optional remote status.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category name to filter by"
                },
                "remote_only": {
                    "type": "boolean",
                    "description": "True to filter for remote roles only",
                    "default": False
                },
                "limit": {
                    "type": "integer",
                    "default": 5
                }
            }
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "analyze_skill_gap",
        "description": "Performs a skill gap audit between candidate skills and a specific target job ID. Use when user asks what skills they are missing for a job or how to qualify for a specific role.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "integer",
                    "description": "The target job ID to analyze"
                },
                "candidate_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills the candidate possesses"
                }
            },
            "required": ["job_id", "candidate_skills"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "get_highest_paying_roles",
        "description": "Finds the highest paying job opportunities and internships offering top hourly rates ($51/hr - $125/hr) or high annual salaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 5
                }
            }
        }
    }
}