import ollama

def list_ollama_models():
    """
    List all available models

    :return: list of models
    """

    return [m.model for m in ollama.list()["models"]]



print(list_ollama_models())
