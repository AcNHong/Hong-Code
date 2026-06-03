def toolToAPISchema(tool):
    return {
        "name": tool.get("name",""),
        "description": tool.get("description",lambda x:None)(),
        "input_schema": tool.get("input_schema",lambda x:None)(),
    }


# toolToAPISchema()