role_heading_map = {"system": "System", "user": "User", "assistant": "Assistant"}
heading_role_map = {v: k for k, v in role_heading_map.items()}
roles = set(role_heading_map.keys())
