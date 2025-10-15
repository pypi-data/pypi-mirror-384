## CLX-cli Basics

Local first, cli chat and agentic application that calls the Llama3.2 (Ollama) text completion endpoint by default with a system message and can identify the OS of the current system. This helps ensure that Linux, Mac, and Windows specific commands tend to be more accurate.

## Installation

## From PyPI (Recommended):
```bash
pip install clx-cli
```

Or using uv:
```bash
uv add clx-cli
```

For isolated environments, consider using a virtual environment:
```bash
python -m venv clx_env
source clx_env/bin/activate  # On Windows: clx_env\Scripts\activate
pip install clx-cli
```

Or using uv to create and manage a virtual environment:
```bash
uv venv clx_env
source clx_env/bin/activate  # On Windows: clx_env\Scripts\activate
uv pip install clx-cli
```

## From Source
CLX-cli uses modern Python packaging with pyproject.toml for dependency management:

Installing with -e puts the package in development mode, allowing you to modify the code without reinstalling.

## For Development: 
- Clone this repo to your computer using your terminal.
- `cd ~/<your-directory>/clx-cli/`
- Run `pip install -e .` inside your clx directory

- A "clx-cli" command should be available to use clx from your CLI, e.g. `clx-cli -g "Who was the 45th president of the United States?`

- clx will automatically store questions, responses and agent memory in a local SQLite database located at `~/.clx_cache`

- NOTE: For the script to work, you will need to have Ollama running in the background. To install a desired Ollama model go to https://ollama.com/search

## Setup Requirements

### For Ollama Models (Default - Recommended for Local Use)

1. **Install Ollama**: Visit [ollama.com](https://ollama.com) and follow the installation instructions for your OS
2. **Start Ollama**: Ensure Ollama is running in the background
3. **Pull Required Models**: Run these commands to download the models clx-cli supports:

```bash
# Default model (llama3.2)
ollama pull llama3.2
```

### For OpenAI API (Cloud-based)

If you prefer to use OpenAI's models instead of local Ollama models:

1. **Get an OpenAI API Key**: Sign up at [platform.openai.com](https://platform.openai.com) and create an API key
2. **Set Environment Variable**: Add your API key to your environment:

```bash
# Add to your ~/.zshrc, ~/.bashrc, or ~/.bash_profile
export OPENAI_API_KEY="your-api-key-here"

# Or create a .env file in your project directory
echo "OPENAI_API_KEY=your-api-key-here" > ~/.env
```

#### How to set your OpenAI API key (for non-developers)

**macOS & Linux:**
1. Open your Terminal app.
2. Run this command (replace with your actual key):
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
3. To make it permanent, add the above line to your shell config file:
   - For zsh: `echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc`
   - For bash: `echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc`
4. Reload your shell:
   ```bash
   source ~/.zshrc  # or source ~/.bashrc
   ```

**Windows:**
1. Open Command Prompt.
2. Run:
   ```cmd
   setx OPENAI_API_KEY "your-api-key-here"
   ```
3. Close and reopen Command Prompt for changes to take effect.
4. Alternatively, you can set environment variables via System Properties > Environment Variables.

**.env file (all platforms):**
You can also create a file named `.env` in your project folder and add this line:
```
OPENAI_API_KEY=your-api-key-here
```
Some tools will automatically read this file.

3. **Reload your shell** or run:
```bash
source ~/.zshrc  # or ~/.bashrc
```

**Note**: OpenAI API usage incurs costs based on your usage. Check OpenAI's pricing at [openai.com/pricing](https://openai.com/pricing)


## Model Selection
  
You can choose which Ollama model CLX uses by passing one of these flags before your question:
  
- `-l32` : use `llama3.2` (default)  

To use OpenAI models: 
- `-oa`: use `openai o4-mini`
  
Example:
  
```
clx-cli -l32 -g "List files in my home directory"
clx-cli -oa -g "Who is the president of the United States?"
```

You can also call clx with a **-s** option. This will save any command as a shortcut with whatever name you choose. The first parameter is the name of the command and the second is the command itself in quotes.

```
$> clx-cli -s nap "pmset sleepnow"
   Saving shortcut nap, will return: pmset sleepnow
$> clx-cli -x nap
   Sleeping now...
```

To copy a command directly into the clipboard use the **-c** option. Can be useful if you want to execute the command but you don't trust clx to do so automatically.

CLX has a -g option to ask general questions. The results when you ask a general question will not be formated as a command line. This is useful for asking general questions, historical facts or other information not likely to be formated as a command.

```
$> clx-cli -g "Who was the 23rd president?"
  Herbert Hoover
$> clx-cli -g "What is the meaning of life?"
   42
```

## Agent Mode

CLX includes an agent mode with persistent conversation memory using the **-a** flag. In agent mode, the AI maintains context across multiple interactions, remembering your conversation history even between sessions.

```
$> clx-cli -a
   Entering agent mode. Type 'exit' to end the agent chat.
   Type 'clear' to clear conversation history.
You: What's my name?
Agent: I don't have any information about your name from our conversation.

You: My name is John
Agent: Nice to meet you, John! I'll remember that.

You: exit
   Exiting chat mode.
```

When you restart agent mode later, it will remember previous conversations. Use `clear` to reset the conversation history if needed.

---

This code is free to use under the MIT license.
