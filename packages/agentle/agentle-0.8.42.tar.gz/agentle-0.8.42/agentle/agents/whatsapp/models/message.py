from typing import NotRequired, TypedDict

from agentle.agents.whatsapp.models.audio_message import AudioMessage
from agentle.agents.whatsapp.models.document_message import DocumentMessage
from agentle.agents.whatsapp.models.image_message import ImageMessage
from agentle.agents.whatsapp.models.message_context_info import MessageContextInfo
from agentle.agents.whatsapp.models.video_message import VideoMessage


class Message(TypedDict):
    """Conteúdo da mensagem WhatsApp.

    Attributes:
        conversation: Texto da mensagem (para mensagens de texto simples)
        imageMessage: Dados da imagem (para mensagens com imagem)
        documentMessage: Dados do documento (para mensagens com documento)
        audioMessage: Dados do áudio (para mensagens de áudio)
        videoMessage: Dados do vídeo (para mensagens de vídeo)
        messageContextInfo: Informações de contexto da mensagem (opcional)
        base64: Conteúdo da mídia codificado em base64 (opcional)
    """

    conversation: NotRequired[str]
    imageMessage: NotRequired[ImageMessage]
    documentMessage: NotRequired[DocumentMessage]
    audioMessage: NotRequired[AudioMessage]
    videoMessage: NotRequired[VideoMessage]
    messageContextInfo: NotRequired[MessageContextInfo]
    base64: NotRequired[str]
