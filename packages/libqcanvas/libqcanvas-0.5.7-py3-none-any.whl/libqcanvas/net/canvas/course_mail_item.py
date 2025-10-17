from dataclasses import dataclass
from datetime import datetime

from libqcanvas.gql_queries import ConversationParticipant


@dataclass
class CourseMailItem:
    id: str
    subject: str
    body: str
    author_name: str
    course_name: str
    course_id: str
    date: datetime

    @staticmethod
    def from_query_result(data: ConversationParticipant) -> "CourseMailItem":
        outer_data = data.conversation
        message_data = outer_data.conversation_messages_connection.nodes[0]

        return CourseMailItem(
            id=message_data.q_id,
            body=message_data.body,
            author_name=message_data.author.name,
            course_name=outer_data.context_name,
            subject=outer_data.subject,
            course_id=outer_data.context_id,
            date=message_data.created_at,
        )
