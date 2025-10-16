import requests


class AIClient:
    def __init__(self,
                 api_key="io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjE3MzkwYTJhLWU1YTUtNDQyZC1iZmNhLTY0MzE2NTVhMjM4MiIsImV4cCI6NDkxNDE2MTE5Mn0.hDS82ASMqgoje1HO94OngWQil5BZrdhNMSDnV9uBuWtCP3RHqdrvkkoAOPJYcg6qNvKGuZoXqWq-EfYwNIuh6g"):
        self.api_key = api_key
        self.model = "deepseek-ai/DeepSeek-R1-0528"

    def set_model(self, model_name: str = None):
        """
        Устанавливает модель ИИ. Если имя модели не указано,
        выводит список доступных моделей для выбора.
        """
        if model_name:
            self.model = model_name
            return

        url = "https://api.intelligence.io.solutions/api/v1/models"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            print("Доступные модели:")
            for model in data['data']:
                print(f"- {model['id']}")

            self.model = input("\nВведите название модели: ").strip()
            print(f"Модель установлена: {self.model}")

        except Exception as e:
            print(f"Ошибка при получении моделей: {str(e)}")
            self.model = "deepseek-ai/DeepSeek-R1-0528"

    def ask_AI(self, message: str, raw: bool = False) -> str:
        """
        Отправляет запрос к ИИ и возвращает ответ.

        :param message: Текст запроса
        :param raw: Если True, возвращает полный ответ без обработки
        :return: Ответ ИИ
        """
        url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()

            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("Некорректный ответ от API")

            text = response_data["choices"][0]['message']['content']

            if raw:
                return text

            # Обработка ответа
            if "</think>\n" in text:
                return text.split("</think>\n")[1]
            return text

        except Exception as e:
            print(f"Ошибка запроса: {str(e)}")
            return ""