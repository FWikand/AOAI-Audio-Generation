import json

def get_summary_card_tool(goal="general_summary", goal_instruction=None):
    """Return the summary card tool definition based on the selected goal."""
    base_properties = {
        "title": {
            "type": "string",
            "description": "A concise title for the summary"
        }
    }
    
    if goal == "custom" and goal_instruction:
        return {
            "type": "function",
            "function": {
                "name": "create_summary_card",
                "description": f"Create a summary card based on the custom goal: {goal_instruction}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        **base_properties,
                        "custom_analysis": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "heading": {
                                        "type": "string",
                                        "description": "A descriptive heading for this section of the analysis"
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": f"Detailed content addressing this aspect of the custom goal: {goal_instruction}"
                                    }
                                },
                                "required": ["heading", "content"]
                            },
                            "description": f"Analysis sections addressing the custom goal: {goal_instruction}. Break down your analysis into logical sections with clear headings."
                        },
                        "conclusion": {
                            "type": "string",
                            "description": "A concluding statement summarizing the key findings"
                        }
                    },
                    "required": ["title", "custom_analysis"]
                }
            }
        }

    goal_specific_properties = {
        "general_summary": {
            "main_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of main points from the summary"
            },
            "key_highlights": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "highlight": {
                            "type": "string",
                            "description": "The key highlight or insight"
                        },
                        "details": {
                            "type": "string",
                            "description": "Additional details or context"
                        }
                    }
                },
                "description": "Key highlights with details"
            }
        },
        "key_insights": {
            "insights": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "insight": {
                            "type": "string",
                            "description": "A key insight from the document"
                        },
                        "impact": {
                            "type": "string",
                            "description": "The potential impact or importance of this insight"
                        }
                    }
                },
                "description": "List of key insights with their potential impact"
            }
        },
        "action_items": {
            "priority_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The action item to be completed"
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level (High/Medium/Low)"
                        },
                        "timeline": {
                            "type": "string",
                            "description": "Suggested timeline for completion"
                        }
                    }
                },
                "description": "List of prioritized action items"
            }
        },
        "topic_analysis": {
            "key_themes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "theme": {
                            "type": "string",
                            "description": "A major theme or topic"
                        },
                        "analysis": {
                            "type": "string",
                            "description": "Detailed analysis of the theme"
                        }
                    }
                },
                "description": "Major themes and their analysis"
            }
        },
        "recommendations": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "recommendation": {
                            "type": "string",
                            "description": "The specific recommendation"
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Reasoning behind the recommendation"
                        },
                        "implementation": {
                            "type": "string",
                            "description": "Suggested implementation approach"
                        }
                    }
                },
                "description": "List of recommendations with rationale and implementation suggestions"
            }
        }
    }

    # Add conclusion to all goals
    for props in goal_specific_properties.values():
        props["conclusion"] = {
            "type": "string",
            "description": "A concluding statement or summary"
        }

    # Get the properties for the selected goal
    properties = {**base_properties, **goal_specific_properties.get(goal, goal_specific_properties["general_summary"])}

    # Create a list of required fields, ensuring uniqueness
    all_fields = set(properties.keys())
    all_fields.add("title")  # Make sure title is included
    all_fields.discard("conclusion")  # Remove conclusion as it's optional
    required_fields = list(all_fields)

    return {
        "type": "function",
        "function": {
            "name": "create_summary_card",
            "description": "Create a beautifully formatted HTML summary card with sections and styling",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_fields
            }
        }
    }

def process_summary_card(tool_call, goal="general_summary", goal_instruction=None):
    """Process the summary card based on the tool call and goal."""
    try:
        # Get the arguments from the tool call
        arguments = json.loads(tool_call.function.arguments)
        
        if goal == "custom" and goal_instruction:
            custom_sections = []
            for section in arguments.get("custom_analysis", []):
                custom_sections.append(f"""
                    <div class="mb-4">
                        <h3 class="text-lg font-semibold mb-2">{section['heading']}</h3>
                        <p class="text-gray-700">{section['content']}</p>
                    </div>
                """)
            
            return f"""
                <div class="summary-card">
                    <h2 class="text-xl font-bold mb-4">{arguments['title']}</h2>
                    <div class="custom-analysis">
                        {"".join(custom_sections)}
                    </div>
                </div>
            """

        # Rest of the existing code for other goals
        goal_specific_html = {
            "general_summary": lambda data: f"""
                <div class="main-points mb-6">
                    <h3 class="text-lg font-semibold mb-2">Main Points</h3>
                    <ul class="list-disc pl-5 space-y-2">
                        {''.join(f'<li>{point}</li>' for point in data['main_points'])}
                    </ul>
                </div>
                
                <div class="key-highlights mb-6">
                    <h3 class="text-lg font-semibold mb-2">Key Highlights</h3>
                    <div class="space-y-4">
                        {''.join(
                            f'''
                            <div class="highlight-card bg-gray-50 p-4 rounded-lg">
                                <p class="font-medium text-indigo-600">{highlight['highlight']}</p>
                                <p class="text-gray-600 mt-1">{highlight['details']}</p>
                            </div>
                            '''
                            for highlight in data['key_highlights']
                        )}
                    </div>
                </div>
            """,
            "key_insights": lambda data: f"""
                <div class="insights mb-6">
                    <h3 class="text-lg font-semibold mb-2">Key Insights</h3>
                    <div class="space-y-4">
                        {''.join(
                            f'''
                            <div class="insight-card bg-gray-50 p-4 rounded-lg">
                                <p class="font-medium text-indigo-600">{insight['insight']}</p>
                                <p class="text-gray-600 mt-1">Impact: {insight['impact']}</p>
                            </div>
                            '''
                            for insight in data['insights']
                        )}
                    </div>
                </div>
            """,
            "action_items": lambda data: f"""
                <div class="action-items mb-6">
                    <h3 class="text-lg font-semibold mb-2">Priority Actions</h3>
                    <div class="space-y-4">
                        {''.join(
                            f'''
                            <div class="action-card bg-gray-50 p-4 rounded-lg border-l-4 {get_priority_color(action['priority'])}">
                                <p class="font-medium text-indigo-600">{action['action']}</p>
                                <p class="text-gray-600">Priority: {action['priority']}</p>
                                <p class="text-gray-600">Timeline: {action['timeline']}</p>
                            </div>
                            '''
                            for action in data['priority_actions']
                        )}
                    </div>
                </div>
            """,
            "topic_analysis": lambda data: f"""
                <div class="themes mb-6">
                    <h3 class="text-lg font-semibold mb-2">Key Themes</h3>
                    <div class="space-y-4">
                        {''.join(
                            f'''
                            <div class="theme-card bg-gray-50 p-4 rounded-lg">
                                <p class="font-medium text-indigo-600">{theme['theme']}</p>
                                <p class="text-gray-600 mt-1">{theme['analysis']}</p>
                            </div>
                            '''
                            for theme in data['key_themes']
                        )}
                    </div>
                </div>
            """,
            "recommendations": lambda data: f"""
                <div class="recommendations mb-6">
                    <h3 class="text-lg font-semibold mb-2">Recommendations</h3>
                    <div class="space-y-4">
                        {''.join(
                            f'''
                            <div class="recommendation-card bg-gray-50 p-4 rounded-lg">
                                <p class="font-medium text-indigo-600">{rec['recommendation']}</p>
                                <p class="text-gray-600 mt-2"><strong>Rationale:</strong> {rec['rationale']}</p>
                                <p class="text-gray-600 mt-1"><strong>Implementation:</strong> {rec['implementation']}</p>
                            </div>
                            '''
                            for rec in data['recommendations']
                        )}
                    </div>
                </div>
            """
        }

        # Get the appropriate HTML generator for the goal
        html_generator = goal_specific_html.get(goal, goal_specific_html["general_summary"])
        
        return f"""
        <div class="summary-card">
            <h2 class="text-2xl font-bold mb-4">{arguments['title']}</h2>
            
            {html_generator(arguments)}
            
            {f'<div class="conclusion mb-4"><p class="italic text-gray-700">{arguments["conclusion"]}</p></div>' if 'conclusion' in arguments else ''}
        </div>
        """
    except KeyError as e:
        # If a required field is missing, return a simple formatted version of the data
        return f"""
        <div class="summary-card">
            <h2 class="text-2xl font-bold mb-4">{arguments.get('title', 'Summary')}</h2>
            <div class="content mb-6">
                <p class="text-gray-600">{str(arguments)}</p>
            </div>
        </div>
        """
    except Exception as e:
        return f"""
        <div class="summary-card">
            <h2 class="text-2xl font-bold mb-4">Error Processing Summary</h2>
            <div class="content mb-6">
                <p class="text-red-600">An error occurred while processing the summary: {str(e)}</p>
            </div>
        </div>
        """

def get_priority_color(priority):
    """Return the appropriate border color class based on priority level."""
    colors = {
        "High": "border-red-500",
        "Medium": "border-yellow-500",
        "Low": "border-green-500"
    }
    return colors.get(priority, "border-gray-500") 