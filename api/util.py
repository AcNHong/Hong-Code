from tools.Tool import toolDef


def toolToAPISchema(tools:list[toolDef],**kwargs):
    base_tools = []
    for tool in tools:
       base =  {
        "name": tool.name,
        "description": tool.prompt(**kwargs),
        "input_schema": tool.input_schema
        }
       base_tools.append(base)

    return base_tools



