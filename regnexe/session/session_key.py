class SessionKey:
    """Maps the three-dimensional (app_id, user_id, session_id) space to a LangGraph thread_id."""

    def to_thread_id(self, app_id: str, user_id: str, session_id: str) -> str:
        return f"{app_id}:{user_id}:{session_id}"

    def from_thread_id(self, thread_id: str) -> tuple[str, str, str]:
        parts = thread_id.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid thread_id {thread_id!r}: expected 'app_id:user_id:session_id'")
        return parts[0], parts[1], parts[2]
