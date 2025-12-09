class PolishingService:
    def __init__(self, ai_client):
        self.ai_client = ai_client

    def polish_text(self, text):
        # 调用AI客户端进行文本润色
        polished_text = self.ai_client.request_polishing(text)
        return polished_text

    def batch_polish_texts(self, texts):
        # 批量处理文本润色
        polished_texts = []
        for text in texts:
            polished_text = self.polish_text(text)
            polished_texts.append(polished_text)
        return polished_texts

    def set_ai_client(self, ai_client):
        self.ai_client = ai_client