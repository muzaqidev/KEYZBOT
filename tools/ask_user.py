"""Ask user tool — interactive user input during agent execution."""

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Ask the user a question to get input, clarification, or a decision. Use when you need user guidance before proceeding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user"
                    },
                    "options": {
                        "type": "array",
                        "description": "Optional list of choices for the user to pick from",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        },
                        "maxItems": 4,
                        "minItems": 2
                    },
                    "multi_select": {
                        "type": "boolean",
                        "description": "Allow selecting multiple options (default false)"
                    }
                },
                "required": ["question"]
            }
        }
    }
]

TOOL_NAMES = {"ask_user"}

def execute(name, args, work_dir=None):
    if name == "ask_user":
        question = args.get("question", "")
        options = args.get("options", [])
        multi = args.get("multi_select", False)

        if not question:
            return "Error: No question provided"

        result = f"[ASK_USER] {question}"
        if options:
            result += "\n"
            for i, opt in enumerate(options, 1):
                label = opt.get("label", f"Option {i}")
                desc = opt.get("description", "")
                if desc:
                    result += f"  {i}. {label} — {desc}\n"
                else:
                    result += f"  {i}. {label}\n"
            if multi:
                result += "(Select multiple)"
            else:
                result += "(Select one)"
        return result
    return f"Unknown tool: {name}"
