from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from .config import settings


class OutputFormat(BaseModel):
    message_to_user: str = Field(..., description="A short, witty, or helpful remark for the user. Do NOT include the command in this field.")
    command: str = Field(..., description="The single, executable shell command that answers the user's query.")
    generalized_command: str = Field(..., description="The generalized version of the command to execute in the shell")

def get_llm_client():
    return init_chat_model(model=settings.llm_model_name, model_provider=settings.llm_model_provider, api_key=settings.llm_api_key).with_structured_output(OutputFormat)

llm = get_llm_client()

def get_results_from_llm(data: dict) -> OutputFormat:

    prompt = f"""You are a sassy but helpful shell command assistant. Your job is to help users learn commands, not just look them up.

User query: {data.get('user_query', '')}

User's shell type: {data.get('shell_type', 'unknown')}

YOUR PERSONALITY:
- Be conversational and natural—vary your responses
- If someone keeps asking similar things, gently call it out AND help them remember
- Teaching moments should feel organic, not formulaic
- Keep responses short (2-3 lines max usually)
- Only be sassy when the context clearly shows they've been here before

WHEN YOU SEE REPETITION IN CONTEXT:
- Notice if they're asking the same type of command repeatedly
- If so, slip in a quick memory trick or pattern explanation
- Make it feel like advice from a friend, not a lecture
- Examples:
  "git clone <url> — you know, the 'clone' part literally means 'copy this repo to my machine'"
  "find . -name '*.js' — think of it as 'find WHERE (-name means match this filename)'"

If there's no relevant context, just give them what they need cleanly.

Provide the message/ remark to the user in 'message_to_user', the exact command to run in 'command', and a generalized version of the command in 'generalized_command'.
For generalized_command: use placeholders like <url>, <file>, <directory>, etc. Match existing placeholder names from context if provided. This won't be shown to the user, but helps track command patterns.
"""

    if data.get("context"):
        prompt += f"""
CONTEXT (previous similar commands):
{data.get('context', '')}

Check the times_called—if it's high, they might benefit from understanding WHY the command works, not just WHAT it is. But keep it natural and brief.
"""
    else:
        prompt += "\nNo previous context available—provide straightforward answer."


    response =  llm.invoke(prompt)

    if not isinstance(response, OutputFormat):
        raise ValueError(f"LLM response is not in the expected format. Got: {response}")
    return response

if __name__ == "__main__":
    test_data = {
        "user_query": "How do I list all files in a directory?",
        "context": "Here are some previously asked queries by the user:\n\nGeneralized Command: ls <directory> \n User Queries: list files in /home/user/docs, show me files in /var/logs\n\n"
    }
    result = get_results_from_llm(test_data)
    print(result)