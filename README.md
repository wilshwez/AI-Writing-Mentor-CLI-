# Arthur AI Writer

A simple, beginner-friendly terminal application that lets you chat with
**Arthur** — an AI persona styled as one of the greatest authors in
history — powered by the [Groq API](https://groq.com/).

Arthur can help you write stories, improve your prose, brainstorm ideas,
build characters and worlds, write poems, proofread text, explain
writing techniques, and generate full book outlines.

---

## Project Structure

```text
ai_writer/
│
├── app.py           
├── writer.py         
├── config.py           
├── prompts.py         
├── requirements.txt      
├── .env.example          
├── .gitignore             
├── LICENSE                  
└── README.md
```

---

## Installation

1. **Clone or download this project**, then move into the folder:

   ```bash
   cd ai_writer
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## API Key Configuration

1. Get a free Groq API key from <https://console.groq.com/keys>.

2. Copy the example env file to create your own local `.env`:

   ```bash
   cp .env.example .env
   ```

3. Open the new `.env` file and replace the placeholder with your real key:

   ```env
   GROQ_API_KEY=your_real_key_here
   ```

   **Never commit your real API key to version control.** The included
   `.gitignore` already excludes `.env`, so this is handled for you as
   long as you don't rename or force-add the file.

---

## Running the Project

### Interactive mode (default)

```bash
python app.py
```

This drops you into a persistent prompt where you can either:

- **Chat freely** — just type a message and press Enter. Conversation
  history is kept for the session, so follow-ups like "make it shorter"
  work naturally.
- **Use slash commands** for specific writing tasks:

```text
Arthur — AI Writing Mentor CLI
Type /help for commands, or just start chatting.

> /story a lighthouse keeper who finds a message in a bottle
> /poem hope
> /brainstorm 5 cozy mystery ideas
> /improve The dog run fast and it was happy.
> /help
> /clear
> /quit
```

Run `/help` inside the session at any time to see the full command list.

### Headless one-shot mode

For scripts, pipes, or automation, pass a prompt directly with `-p` and
Arthur replies once and exits — no interactive session opens:

```bash
python app.py -p "Write a haiku about autumn"
python app.py -p "Brainstorm 5 sci-fi story ideas" --output-format json
echo "Improve this: the dog run fast" | python app.py -p -
```

Use `--output-format json` for machine-readable output you can pipe into
other tools.

Run `python app.py --help` for the full list of flags.

---

## Example Usage

```text
> /story A lighthouse keeper who finds a message in a bottle

╭─ Arthur — Write a short story ─────────────────────────────╮
│ The Lighthouse at Cradle Point                              │
│ ...                                                          │
╰───────────────────────────────────────────────────────────╯
```

```text
> /brainstorm 5 cozy mystery novels set in small towns

╭─ Arthur — Brainstorm ideas ────────────────────────────────╮
│ 1. A retired baker...                                       │
│ ...                                                          │
╰───────────────────────────────────────────────────────────╯
```

```text
> Can you make that idea darker?

╭─ Arthur ────────────────────────────────────────────────────╮
│ Certainly. Let's lean into something with real teeth...     │
╰───────────────────────────────────────────────────────────╯
```

```bash
$ python app.py -p "Write a poem about hope"
Hope is the thread that...
```

---

## Project Architecture

- **`config.py`** — Loads `GROQ_API_KEY` from `.env`, validates it, and
  exits with a friendly message if it's missing.
- **`prompts.py`** — Defines Arthur's permanent system prompt (his
  personality) and small functions that build task-specific user
  prompts (e.g. `story_prompt()`, `brainstorm_prompt()`).
- **`writer.py`** — Defines `ArthurWriter`, a class wrapping the Groq
  chat completions API. Includes:
  - A core `chat()` method with retry-with-backoff logic for rate
    limits, connection errors, and transient server errors. Accepts an
    optional `use_history=True` flag so interactive sessions keep
    conversational context across turns.
  - Convenience methods (`generate_story`, `improve_text`, etc.) that
    build the right prompt and call `chat()`.
- **`app.py`** — The CLI entry point. Supports an interactive session
  with slash commands (`/story`, `/poem`, `/brainstorm`, etc.) and
  free-text chat, plus a headless one-shot mode (`-p "..."`) for
  scripting and automation. Uses `rich` for nicer formatting if it's
  installed.

This separation of concerns means you can:
- Swap out the terminal UI for a web UI without touching `writer.py`.
- Change Arthur's personality by editing only `prompts.py`.
- Change the underlying model/provider by editing only `config.py` /
  `writer.py`.

---

## Troubleshooting

**"ERROR: Missing or invalid GROQ_API_KEY"**
Make sure `.env` exists in the project root and contains a real key,
not the placeholder text.

**"[Error] Groq API returned status 401"**
Your API key is invalid or expired. Generate a new one at
<https://console.groq.com/keys>.

**"[Error] Groq API returned status 429" / rate limited repeatedly**
You're sending requests too quickly for your plan's limits. Wait a
moment and try again, or check your usage at the Groq console.

**Connection errors**
Check your internet connection. The app will automatically retry a few
times with increasing delays before giving up.

**`ModuleNotFoundError: No module named 'groq'`**
Run `pip install -r requirements.txt` again, and make sure your virtual
environment is activated.

---

## Future Improvements

- Save conversation history to a file so you can revisit past sessions.
- Add a "save response to file" option after each generation.
- Support streaming responses (token-by-token output) for a more
  interactive feel.
- Add a web-based front end (e.g. Flask or FastAPI + HTML) on top of
  the same `ArthurWriter` class.
- Let users choose between multiple Groq models from the menu.
- Add unit tests for `prompts.py` and `writer.py`.
