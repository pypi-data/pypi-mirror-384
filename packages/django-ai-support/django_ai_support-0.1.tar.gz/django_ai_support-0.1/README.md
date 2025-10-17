# django-ai-support

This library is powered by langchain and langgraph to make easy AI support for your online shop or any website you want to create with Django.

[This is used Agent workflow](https://langchain-ai.github.io/langgraph/tutorials/workflows/#agent)

## Get started

### settings

Settings should be something like this 

```python
AI_SUPPORT_SETTINGS = {
    "TOOLS": [],
    "SYSTEM_PROMPT": "You are the supporter of a bookstore website.",
    "LLM_MODEL": model,
}
```

TOOLS: tools are for your AI model.

SYSTEM_PROMPT: This is important for your AI support, but the default prompt is: ```You are the supporter of a bookstore website.``` As you see.

LLM_MODEL: your chat model.  like this:

```python
model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
```

[see more](https://python.langchain.com/docs/integrations/chat/)

*Be careful*: LLM_MODEL can not be None.

### config

Additionally, you can integrate your tools within your apps and add them to `TOOLS`.

For example, I have an app with the name of book. and this is inside of my `tools.py` file:

```python
from langchain_core.tools import tool

from .models import Book

@tool(description="this is to get list of book with a price")
def get_books_with_price(price:int) -> str:
    """
    get book with input price

    Args:
        price (int): price. in dollars

    Returns:
        str: list of books.
    """
    text = ""

    for book in Book.objects.filter(price=price).select_related("author"):
        book_detail = f"book name: {book.name}, book price: {book.price}, Author: {book.author.first_name} {book.author.last_name}"
        text += book_detail + "\n"

    return text


```

After that, I can add this tool easily. This is inside my `apps.py` file:

```python
from django.apps import AppConfig


class BookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'book'

    def ready(self):
        from .tools import get_books_with_price as  my_tool
        from django_ai_support.conf import append_tools

        append_tools([my_tool])


```

[read more about tool calling in langchain](https://langchain-ai.github.io/langgraph/how-tos/tool-calling/#dynamically-select-tools)


### API

Now, you can use the chat API to talk with your AI support:

```python
from django.urls import path

from django_ai_support.views import ChatAiSupportApi

urlpatterns = [
    path("ai/", ChatAiSupportApi.as_view())
]
```

![swagger](./images/swagger-example.png)

