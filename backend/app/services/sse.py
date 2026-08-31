def format_sse_data(content: object) -> str:
    """编码 SSE data 事件，同时保留模型分片中的换行。"""
    lines = str(content).split("\n")
    return "\n".join(f"data: {line}" for line in lines) + "\n\n"
