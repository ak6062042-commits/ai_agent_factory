from backend.app.config import KEEP_CHAT_SESSIONS

# Baseline from my last project

class History:
    def __init__(self):
        self.chat_sessions: dict[str, list[dict]] = {}

    def _key(self, tenant_id: str, agent_id: str, session_id: str) -> str:
        return f"{tenant_id}:{agent_id}:{session_id}"

    def add_message(self, tenant_id: str, agent_id: str, session_id: str, role: str, content: str):
        key = self._key(tenant_id, agent_id, session_id)
        if key not in self.chat_sessions:
            self.chat_sessions[key] = []

        self.chat_sessions[key].append({"role": role, "content": content})
        self.chat_sessions[key] = self.chat_sessions[key][-KEEP_CHAT_SESSIONS:]

    def get_history(self, tenant_id: str, agent_id: str, session_id: str) -> list[dict]:
        return self.chat_sessions.get(self._key(tenant_id, agent_id, session_id), [])

    def build_conversation_string(self, tenant_id: str, agent_id: str, session_id: str) -> str:
        history = self.get_history(tenant_id, agent_id, session_id)
        if not history:
            return ""

        lines = [f"{msg['role'].upper()}: {msg['content']}" for msg in history]
        return "\n".join(lines)