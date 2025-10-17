from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from ..messages import MessageRole, MessageContent, MessageDeliveryStatus

class MessagesCreateRequest(BaseModel):
    role: MessageRole = Field(..., description="Papel do remetente da mensagem (user, assistant)")
    content: MessageContent = Field(..., description="Conteúdo da mensagem com tipo e dados")
    provider_message_id: Optional[str] = Field(None, description="ID da mensagem no sistema externo")
    replied_provider_message_id: Optional[str] = Field(None, description="ID da mensagem sendo respondida no sistema externo")

class MessagesUpdateRequest(BaseModel):
    provider_message_id: Optional[str] = Field(None, description="Novo ID da mensagem no sistema externo")
    replied_provider_message_id: Optional[str] = Field(None, description="Novo ID da mensagem sendo respondida no sistema externo")
    delivery_status: Optional[MessageDeliveryStatus] = Field(None, description="Status de entrega da mensagem")
    delivery_error_code: Optional[int] = Field(None, description="Código de erro na entrega")
    delivery_error_message: Optional[str] = Field(None, description="Mensagem de erro na entrega")
    delivered_at: Optional[datetime] = Field(None, description="Timestamp de quando a mensagem foi entregue")

class MessagesSearchRequest(BaseModel):
    session_id: str = Field(..., description="ID da sessão para buscar mensagens")
    provider_message_id: Optional[str] = Field(None, description="Filtrar por ID da mensagem no sistema externo")
    replied_provider_message_id: Optional[str] = Field(None, description="Filtrar por ID externo da mensagem sendo referenciada pelo reply")
    offset: Optional[int] = Field(None, description="Número de registros para pular")
    limit: Optional[int] = Field(None, description="Limite máximo de registros retornados")

class MessagesSendRequest(BaseModel):
    content: MessageContent = Field(..., description="Conteúdo da mensagem com tipo e dados")
    role: MessageRole = Field(..., description="tipo do remetente da mensagem (user, assistant)")
    organization_id: str = Field(..., description="ID da organização")
