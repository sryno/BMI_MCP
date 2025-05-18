import json
from openai import OpenAI


NUTRITION_PROMPT = """
## Instructions
You are an intelligent matching agent. Your task is to evaluate a list of food item descriptions and determine which 
one best matches a given query string. Follow all guidelines precisely and do not deviate from the required output 
structure.

## Goal
Identify and return the food item from the provided list that most closely corresponds to the query string. Your 
selection should prioritize:
- Direct semantic alignment with the query (e.g., "apple" → "red delicious, slices, raw")
- Items that represent a single, whole, or primary ingredient rather than composite or processed foods
- High-confidence matches based on meaning, not just text similarity

## Return Format
Return your response as a single JSON object in one of the following formats:

**If a confident match is found:**
```json
{"index": 2, "description": "red delicious, slices, raw"}
```

**If no confident match is found:**
```json
{"index": null, "description": "No confident match found"}
```

Return ONLY this JSON object and nothing else.

## Warnings
- Do NOT return explanations, ranked lists, or multiple results.
- Do NOT return partial matches unless they clearly and confidently reflect the intent of the query.
- Do NOT include any commentary or formatting outside of the required JSON.

## Contextual Information
- The query string is a simple food term (e.g., "apple", "flank steak", "cottage cheese").
- The food item list is presented as a JSON object with a search_results array containing food descriptions and their 
indices.
- Your job is to select the one description that best represents the food item described by the query string.

## Example Input
```json
{
  "query": "apple",
  "search_results": [
    {"index": 0, "description": "apple, croissant"},
    {"index": 1, "description": "apple pie"},
    {"index": 2, "description": "red delicious, slices, raw"}
  ]
}
```

## Example Output
```json
{"index": 2, "description": "red delicious, slices, raw"}
```
"""


def get_food_item_from_llm(query: str, search_results: list) -> dict:
    """Get the most likely food item from the LLM."""
    client = OpenAI()

    # Format the search results
    llm_input = json.dumps({
        "query": query,
        "search_results": [{"index": i, "description": sr} for i, sr in enumerate(search_results)]
    })

    response = client.responses.create(
        model="gpt-4.1-nano",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": NUTRITION_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": llm_input
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "json_object"
            }
        },
        temperature=0.6,
        max_output_tokens=256,
        top_p=0.95,
        store=False
    )
    return json.loads(response.output_text)