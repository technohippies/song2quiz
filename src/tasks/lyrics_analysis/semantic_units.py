# # semantic_units.py
# @task
# async def analyze_semantic_units(line: str) -> Dict:
#     """Analyze semantic units in the line"""
#     prompt = get_semantic_prompt(line)
#     result = await llm.analyze(prompt)
#     return {
#         "semantic_units": [
#             {
#                 "text": line,
#                 "type": "DECLARATIVE_STATEMENT",
#                 "meaning": "...",
#                 "layers": [...],
#                 "annotation": "...",
#                 "normalized_text": "..."
#             }
#         ]
#     }