from typing import Any, NotRequired, TypedDict


class ImageMessage(TypedDict):
    """Dados de uma mensagem com imagem do WhatsApp.

    Attributes:
        url: URL da imagem no servidor WhatsApp
        mimetype: Tipo MIME da imagem (ex: "image/jpeg")
        fileSha256: Hash SHA256 do arquivo para verificação de integridade
        fileLength: Tamanho do arquivo em bytes (como string)
        height: Altura da imagem em pixels
        width: Largura da imagem em pixels
        mediaKey: Chave de criptografia para decodificar a mídia
        fileEncSha256: Hash SHA256 do arquivo criptografado
        directPath: Caminho direto para download da mídia
        mediaKeyTimestamp: Timestamp da chave de mídia
        jpegThumbnail: Thumbnail da imagem em base64 (opcional)
        contextInfo: Informações de contexto da mensagem (opcional)
        firstScanSidecar: Dados do primeiro scan de segurança (opcional)
        firstScanLength: Tamanho do primeiro scan (opcional)
        scansSidecar: Dados dos scans de segurança subsequentes (opcional)
        scanLengths: Lista com tamanhos dos scans realizados (opcional)
        midQualityFileSha256: Hash SHA256 da versão de qualidade média (opcional)
    """

    url: str
    mimetype: NotRequired[str]
    caption: NotRequired[str]
    fileSha256: NotRequired[str]
    fileLength: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]
    mediaKey: NotRequired[str]
    fileEncSha256: NotRequired[str]
    directPath: NotRequired[str]
    mediaKeyTimestamp: NotRequired[str]
    jpegThumbnail: NotRequired[str]
    contextInfo: NotRequired[dict[str, Any]]
    firstScanSidecar: NotRequired[str]
    firstScanLength: NotRequired[int]
    scansSidecar: NotRequired[str]
    scanLengths: NotRequired[list[int]]
    midQualityFileSha256: NotRequired[str]
