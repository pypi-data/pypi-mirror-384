#!/usr/bin/env python3
import requests
import sqlite3
import sys
import json
from os.path import expanduser
import os
import pyperclip
from openai import OpenAI, OpenAIError, RateLimitError
from dotenv import load_dotenv

load_dotenv()

# Handlers for local agent memory --


def load_agent_memory():
    global cache
    memory_items = cache.execute(
        "SELECT memory_item FROM agent_memory ORDER BY timestamp ASC"
    ).fetchall()
    return [item[0] for item in memory_items]


def save_agent_memory_item(memory_item):
    global cache
    cache.execute(
        "INSERT INTO agent_memory (memory_item) VALUES (?)", (memory_item,))
    cache.commit()


def clear_agent_memory():
    global cache
    cache.execute("DELETE FROM agent_memory")
    cache.commit()
# local agent memory --


def initDB():
    global cache
    home = expanduser("~")
    cache = sqlite3.connect(home + "/.clx_cache")
    cache.execute("""
                    CREATE TABLE IF NOT EXISTS questions
                    (id INTEGER PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    count INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")  # Add timestamp column

    # Create conversations table
    cache.execute("""
                    CREATE TABLE IF NOT EXISTS conversations
                    (id INTEGER PRIMARY KEY,
                    messages TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    # Create agent_memory table
    cache.execute("""
                    CREATE TABLE IF NOT EXISTS agent_memory
                    (id INTEGER PRIMARY KEY,
                    memory_item TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")


def closeDB():
    global cache
    cache.commit()
    cache.close()


def call_model(prompt, system_message="", model="llama3.2", stream_to_stdout=True):
    full_prompt = f"{system_message}\n{prompt}" if system_message else prompt

    if "openai" in model:
        try:
            client = OpenAI()
            result = client.responses.create(
                model="o4-mini",
                input=full_prompt
            ).output_text
            return result
        except RateLimitError as e:
            print("Rate Limit Error Ocurred: ", e)
            print(
                "Insufficient quota: Please check OpenAI API usage and billing details.")
            sys.exit(1)
        except OpenAIError as e:
            print("Open AI Error Occurred: ", e)
            sys.exit(1)
    else:
        url = os.environ.get(
            "OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/") + "/api/generate"
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": True,   # keep streaming from server for fast first token
            "options": {
                "num_predict": 256,
            },
        }

        proxies = {"http": None, "https": None}
        headers = {"Accept": "text/event-stream"}

        out = []
        with requests.post(
            url, json=payload, stream=True, timeout=(5, 1200),
            proxies=proxies, headers=headers
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="ignore")
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                token = chunk.get("response", "")
                if token:
                    if stream_to_stdout:
                        sys.stdout.write(token)
                        sys.stdout.flush()
                    out.append(token)

                if chunk.get("done"):
                    break

        return "".join(out)

    # else:
    #     # This is a text completion, not a chat completion. Will need to refactor to the messages array to add context.
    #     payload = {
    #         "model": model,
    #         "prompt": full_prompt,
    #         "stream": False
    #     }
    #     # Fully local inference via ollama
    #     response = requests.post("http://localhost:11434/api/generate",
    #                              json=payload)

    #     result = response.json()["response"]

    # return result


def run_clx(argv):
    already_streamed = False

    global sys
    # Initialize argv
    sys.argv = argv

    # Model selection flags: -l32 for llama3.2, -oa for openai-o4-mini
    model_name = "llama3.2"
    filtered_argv = [argv[0]]

    # Valid flags that should be recognized
    valid_flags = {"-l32", "-oa", "-a", "-x", "-c", "-g", "-m", "-s", "-h"}

    for arg in argv[1:]:
        if arg == "-l32":
            model_name = "llama3.2"
        elif arg == "-oa":
            model_name = "openai-o4-mini"
        elif arg.startswith("-") and arg not in valid_flags:
            print(f"Error: Unknown flag '{arg}'")
            print("Valid flags: -l32, -oa, -a, -x, -c, -g, -m, -s, -h")
            sys.exit(1)
        else:
            filtered_argv.append(arg)
    argv = filtered_argv
    sys.argv = argv

    # Raw custom agent mode implemented without a framework. Add flag to use different agentic models: gpt-oss (ollama), gpt-5 (OpenAI API)
    if "-a" in argv:
        argv.remove("-a")  # Remove the -a flag from argv

        # Initialize database first to load agent memory
        initDB()

        # Load existing agent memory from database
        agent_memory = load_agent_memory()

        # Prompt to include conversation history to context
        prompt = """You are an AI assistant. When responding to the user's current prompt, consider the full conversation history to maintain context, consistency, and continuity. If no conversation history is available, treat this as a start of a new conversation and do not attempt to reference earlier messages. Prioritize relevance, clarity, and helpfulness in your response."""
        agent = Agent(agent_memory, prompt)
        print("Entering agent mode. Type 'exit' to end the agent chat.")
        print("Type 'clear' to clear conversation history.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Exiting chat mode.")
                closeDB()
                sys.exit()  # Terminate the program immediately
            elif user_input.lower() == 'clear':
                clear_agent_memory()
                agent.memory = []
                print("Conversation history cleared.")
                continue
            response = agent.run(user_input)
            print("Agent:", response, "\n")

    def checkQ(question_text):
        global cache
        sql = "SELECT id,answer,count FROM questions WHERE question =" + question_text
        answer = cache.execute(
            "SELECT id,answer,count FROM questions WHERE question = ?", (question_text,))
        answer = answer.fetchone()
        if (answer):
            response = answer[1]
            newcount = int(answer[2]) + 1
            counter = cache.execute(
                " UPDATE questions SET count = ? WHERE id = ?", (newcount, answer[0]))
            return (response)
        else:
            return (False)

    def insertQ(question_text, answer_text):
        global cache
        answer = cache.execute(
            "DELETE FROM questions WHERE question = ?", (question_text,))
        answer = cache.execute(
            "INSERT INTO questions (question,answer) VALUES (?,?)", (question_text, answer_text))

        # Insert message history into conversations table
        messages = [{"role": "user", "content": question_text},
                    {"role": "assistant", "content": answer_text}]
        cache.execute(
            "INSERT INTO conversations (messages) VALUES (?)", (json.dumps(messages),))

    def fetchQ(argv):
        question = ""
        # [clx,-x,  What,is,the,date]  # execute the response
        # [clx,What,is, the,date]      # no quotes will work
        # [clx,What is the date]       # with quotes will work
        for a in range(1, len(argv)):
            question = question + " " + argv[a]
        question = question.strip()
        return question

    def parseOptions(question):
        global question_mode    # modes are normal, shortcut and general
        global general_q
        global execute
        global clip
        global shortcut
        global agent_mode
        question_mode = "normal"
        shortcut = ""
        execute = False
        clip = False
        agent_mode = False
        if ("-h" in question) or (question == " "):  # Return basic help info
            print("CLX is a simple utility powered by AI (Ollama)")
            print("""
            Example usage:
            clx how do I copy files to my home directory
            clx "How do I put my computer to sleep
            clx -c "how do I install homebrew?"      (copies the result to clipboard)
            clx -x what is the date                  (executes the result)
            clx -g who was the 22nd president        (runs in general question mode)
            clx -m                                   (prints the converstaion history)
            clx -a                                   (runs in agent mode)
            """)
            exit()

        if ("-m" in question):
            question_mode = "history"

        if ("-x" in question):      # Execute the command
            execute = True
            question = question.replace("-x ", "")

        if ("-c" in question):      # Copy the command to clipboard
            clip = True
            question = question.replace("-c ", "")

        if ("-g" in question):      # General question, not command prompt specific
            question_mode = "general"
            question = question.replace("-g ", "")

        if ("-s" in question):         # Save the command as a shortcut
            question_mode = "shortcut"
            question = argv[2]
            shortcut = argv[3]

        return (question)

    def fetch_previous_prompts():
        global cache

        prompts = cache.execute(
            "SELECT messages FROM conversations ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()
        previous_prompts = []

        for prompt in prompts:
            messages = json.loads(prompt[0])
            previous_prompts.extend(messages)

        return previous_prompts

    # Detect the platform. This helps with platform specific paths
    # and system specific options for certain commands
    platform = sys.platform
    if platform == "darwin":
        platform = "Mac"
    elif platform == "win32":
        platform = "Windows"
    else:
        platform = "Linux"

    question = fetchQ(sys.argv)
    question = parseOptions(question)

    # If we change our training/prompts, just delete the cache and it'll
    # be recreated on future runs.
    home = expanduser("~")
    initDB()

    # check if we're saving a shortcut
    # then check if there's an aswer in our cache
    # then execute a GPT request as needed

    if (question_mode == "shortcut"):
        insertQ(question, shortcut)
        print("Saving Shortcut")
    elif (question_mode == "history"):
        cache_answer = False
    else:
        cache_answer = False
        cache_answer = checkQ(question)

    # response = ""
    if not (cache_answer) and ((question_mode == "general") or (question_mode == "normal")):
        temp_question = question
        if not ("?" in question):
            temp_question = question + "?"  # GPT produces better results
            # if there's a question mark.
            # using a temp variable so the ? doesn't get cached

        if (question_mode == "general"):
            system_message = "You are a helpful assistant. Answer the user's question in the best and most concise way possible."
        else:  # question_mode is "normal"
            system_message = f"You are a command line translation tool for {platform}. You will provide a concise answer to the user's question with the correct command."

        # This legacy code was used to handle passing the context to clx via the chat messages array
        # Fetch previous prompts from the cache
        previous_prompts = fetch_previous_prompts()

        # prompt = [{"role": "system", "content": system_message}] + \
        #     previous_prompts

        # prompt += [{"role": "user", "content": temp_question}]

        # response = client.chat.completions.create(model="gpt-4o-mini",
        #                                           messages=prompt,
        #                                           temperature=0,
        #                                           max_tokens=250,
        #                                           top_p=1,
        #                                           frequency_penalty=0,
        #                                           presence_penalty=0)
        # result = response.choices[0].message.content
        stream_live = True  # set to False if you want quiet mode
        result = call_model(temp_question, system_message, model_name)
        already_streamed = stream_live
        insertQ(question, result)
    elif question_mode == "history":
        print("CHAT HISTORY (last 10 messages):")
        messages = []
        conversation_history = fetch_previous_prompts()
        for message in conversation_history:
            if message['role'] == 'user':
                messages.append("User: " + message['content'])
            elif message['role'] == 'assistant':
                messages.append("Assistant: " + message['content'] + "\n")
        result = "\n".join(messages)
    else:
        result = cache_answer
        if not (question_mode == "shortcut"):
            print("💾 Cache Hit")

    if clip:
        pyperclip.copy(result)
    if execute:
        print("clx executing: " + result)
        if ("sudo" in result):
            print("Execution canceled, clx will not execute sudo commands.")
        else:
            result = os.system(result)
    else:
        if not (question_mode == "shortcut"):
            if already_streamed:
                sys.stdout.write("\n")
            else:
                print(result)

    closeDB()


class Agent:
    # This is a raw Agent implementation.
    # TODO: Add multiple agents built with different frameworks: Agents SDK, PydanticAI, Langchain, etc. for testing
    def __init__(self, memory, prompt):
        self.memory = memory
        self.prompt = prompt

    def run(self, input):
        # Prevent update memory if a blank or prompt with only spaces is given
        if not input.strip():
            result = "Please type in a prompt"
            return result

        # TODO: Error checking to handle context window overflow
        history = "Converstation History: " + "\n".join(self.memory)
        user_prompt = "User: " + input
        result_input = history + "\n" + user_prompt
        model_output = call_model(result_input, self.prompt)
        result_output = "Assistant: " + model_output

        # Create memory item and save to database
        memory_item = user_prompt + "\n" + \
            result_output.replace('\n', ' ').replace('\r', ' ')
        self.memory.append(memory_item)
        save_agent_memory_item(memory_item)

        # Make sure to remove "Assistant: "
        return result_output[11:]
