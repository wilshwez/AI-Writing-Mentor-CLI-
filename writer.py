import time

from groq import Groq, APIConnectionError, APIStatusError, RateLimitError

from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from prompts import (
    SYSTEM_PROMPT,
    story_prompt,
    improve_prompt,
    continue_prompt,
    brainstorm_prompt,
    character_prompt,
    world_building_prompt,
    poem_prompt,
    proofread_prompt,
    explain_technique_prompt,
    outline_prompt,
)


def create_client(api_key: str) -> Groq:
    """
    Create and return a Groq API client.

    Args:
        api_key: A valid Groq API key.

    Returns:
        Groq: An initialized Groq client instance.
    """
    return Groq(api_key=api_key)


class ArthurWriter:
    """
    A wrapper around the Groq API that always speaks as 'Arthur',
    the AI writing mentor persona defined in prompts.py.
    """

    def __init__(self, client: Groq, model: str = DEFAULT_MODEL):
        self.client = client
        self.model = model
        # Running conversation history (excludes the system prompt, which is
        # always re-added fresh in chat()). Each entry is a {"role", "content"}
        # dict matching the Groq/OpenAI-style message format.
        self.history = []

    def reset_history(self):
        """Clear the conversation history (used by the /clear command)."""
        self.history = []


    # Core chat method - everything else builds on top of this.
    
    def chat(self, user_message: str, max_retries: int = 3,
              use_history: bool = False) -> str:
        """
        Send a message to Arthur and return his reply.

        Includes simple retry-with-backoff logic for transient failures
        (rate limits, connection issues, 5xx server errors).

        Args:
            user_message: The prompt/question to send.
            max_retries: How many times to retry on transient failure.
            use_history: If True, includes prior conversation turns for
                context (used by the interactive loop so follow-ups like
                "continue that" work) and appends this turn to history.

        Returns:
            str: Arthur's response text.
        """
        if use_history:
            messages = (
                [{"role": "system", "content": SYSTEM_PROMPT}]
                + self.history
                + [{"role": "user", "content": user_message}]
            )
        else:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]

        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=DEFAULT_TEMPERATURE,
                    max_tokens=DEFAULT_MAX_TOKENS,
                )
                reply = response.choices[0].message.content.strip()
                if use_history:
                    self.history.append({"role": "user", "content": user_message})
                    self.history.append({"role": "assistant", "content": reply})
                return reply

            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt  # exponential backoff: 2s, 4s, 8s...
                print(f"\n[Rate limited. Retrying in {wait_time}s "
                      f"(attempt {attempt}/{max_retries})...]")
                time.sleep(wait_time)

            except APIConnectionError as e:
                last_error = e
                wait_time = 2 ** attempt
                print(f"\n[Connection issue. Retrying in {wait_time}s "
                      f"(attempt {attempt}/{max_retries})...]")
                time.sleep(wait_time)

            except APIStatusError as e:
                # 4xx/5xx errors from the API itself.
                last_error = e
                if 500 <= e.status_code < 600:
                    # Server-side error: worth retrying.
                    wait_time = 2 ** attempt
                    print(f"\n[Server error {e.status_code}. Retrying in "
                          f"{wait_time}s (attempt {attempt}/{max_retries})...]")
                    time.sleep(wait_time)
                else:
                    # Client-side error (bad request, auth, etc.) - don't retry.
                    return (
                        f"[Error] Groq API returned status {e.status_code}: "
                        f"{e.message}"
                    )

            except Exception as e:
                # Catch-all for anything unexpected (e.g. malformed response).
                last_error = e
                break

        return (
            "[Error] Arthur couldn't reach the Groq API after several attempts. "
            f"Last error: {last_error}"
        )

    
    # Task-specific helper methods - each one builds a tailored prompt
    # and delegates to chat().
    
    def generate_story(self, topic: str) -> str:
        return self.chat(story_prompt(topic))

    def improve_text(self, text: str) -> str:
        return self.chat(improve_prompt(text))

    def continue_story(self, text: str) -> str:
        return self.chat(continue_prompt(text))

    def brainstorm(self, topic: str, count: int = 10) -> str:
        return self.chat(brainstorm_prompt(topic, count))

    def generate_character(self, description: str) -> str:
        return self.chat(character_prompt(description))

    def build_world(self, description: str) -> str:
        return self.chat(world_building_prompt(description))

    def write_poem(self, topic: str) -> str:
        return self.chat(poem_prompt(topic))

    def proofread(self, text: str) -> str:
        return self.chat(proofread_prompt(text))

    def explain_technique(self, technique: str) -> str:
        return self.chat(explain_technique_prompt(technique))

    def generate_outline(self, idea: str) -> str:
        return self.chat(outline_prompt(idea))
