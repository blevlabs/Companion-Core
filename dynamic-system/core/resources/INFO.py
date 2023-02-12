import requests


class info:
    def __init__(self):
        pass

    def research(self, query, link_restriction="NONE"):
        assert requests.get("https://qna-api-staging.faqx.com/health").json()["status"] == "OK", "QnA API is down"
        data = requests.post(url="https://qna-api-staging.faqx.com/faqx",
                             json={"online": True, "temperature": 0.7, "vector_search": True, "relevant_text_len": 10,
                                   "minimal_token_threshold": 250, "database_restriction": False,
                                   "link_limit": 1, "historical_tolerance": 0.9, "dynamic_answer": False,
                                   "dynamic_answer_limit": 3, "embeddings_search": True, "paragraph_split": False,
                                   "domain": "general", "mode": "genQNA", "question": query,
                                   "link": link_restriction}).json()[
            "response"]
        slimmed_response = {"answer": data["answer"], "links": data["links"]}
        return slimmed_response
