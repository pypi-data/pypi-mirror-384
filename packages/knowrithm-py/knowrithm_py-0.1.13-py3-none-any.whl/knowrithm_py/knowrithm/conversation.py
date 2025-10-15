



from typing import Dict, List, Optional

from knowrithm_py.knowrithm.client import KnowrithmClient


class KnowrithmConversation:
    """High-level interface for conversation operations"""
    
    def __init__(self, client: KnowrithmClient, conversation_id: str):
        self.client = client
        self.conversation_id = conversation_id
        self._details = None
    
    def send_message(self, content: str, role: str = "user") -> Dict:
        """Send a message in this conversation"""
        return self.client.messages.send_message(self.conversation_id, content, role)
    
    def get_messages(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get conversation messages"""
        return self.client.messages.list_messages(
            self.conversation_id, 
            limit=limit, 
            offset=offset
        )
    
    def get_details(self, force_refresh: bool = False) -> Dict:
        """Get conversation details with caching"""
        if not self._details or force_refresh:
            self._details = self.client.conversations.get(self.conversation_id)
        return self._details
    
    def end(self, satisfaction_rating: Optional[int] = None) -> Dict:
        """End the conversation"""
        return self.client.conversations.end_conversation(
            self.conversation_id, 
            satisfaction_rating=satisfaction_rating
        )
    
    def archive(self) -> Dict:
        """Archive the conversation"""
        return self.client.conversations.archive(self.conversation_id)

