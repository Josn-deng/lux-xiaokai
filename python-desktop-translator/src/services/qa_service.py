class QAService:
    def __init__(self, ai_client):
        self.ai_client = ai_client

    def ask_question(self, question):
        response = self.ai_client.send_request(question)
        return response

    def get_answer(self, question):
        answer = self.ask_question(question)
        return answer

    def refine_answer(self, answer):
        # Placeholder for answer refinement logic
        return answer.strip() if answer else "No answer provided."