# OpenAI Page

[![PyPI version](https://img.shields.io/pypi/v/ac-py-template.svg)](https://pypi.org/project/openai-page/)
[![Python Version](https://img.shields.io/pypi/pyversions/ac-py-template.svg)](https://pypi.org/project/openai-page/)
[![License](https://img.shields.io/pypi/l/ac-py-template.svg)](https://opensource.org/licenses/MIT)

## Usage

```python
from openai_page import Page

# Example with string data
page = Page[str](
    data=["item1", "item2", "item3"], has_more=True, first_id="item1", last_id="item3"
)
```

Example with custom model

```python
from pydantic import BaseModel


class MyModel(BaseModel):
    id: str
    name: str


page = Page[MyModel](
    data=[MyModel(id="1", name="First"), MyModel(id="2", name="Second")], has_more=False
)
```

---

MIT License
