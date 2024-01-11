import os
import asyncio
import discord
import json
from discord import Client, Intents
from openai import OpenAI

openai = OpenAI(api_key='youropenaikey')
discord_token = "yourdiscordtoken"
assistant_id = "yourassistantid"

intents = Intents.all()
client = Client(intents=intents)

def get_thread(discord_thread):
    try:
        threads = open("threads.json", "r")
    except IOError:
        newfile = open("threads.json", "w")
        newfile.write("{}")
        newfile.close()
        print("initial threads.json written")
        threads = open("threads.json", "r")
    data = json.load(threads)
    openai_thread = data[discord_thread] if discord_thread in data else create_openai_thread(discord_thread)
    threads.close()
    return openai_thread

def create_openai_thread(discord_thread):
    thread_id = openai.beta.threads.create().id
    try:
        threads = open("threads.json", "r+")
    except IOError:
        newfile = open("threads.json", "w")
        newfile.write("{}")
        newfile.close()
        threads = open("threads.json", "r+")
    data = json.load(threads)
    new_thread = "{ \"" + str(discord_thread) + "\" : \"" + str(thread_id) + "\" }"
    new_thread = json.loads(new_thread)
    print("thread to add : " + str(new_thread))
    data.update(new_thread)
    #overwrite threads
    threads.seek(0)
    json.dump(data, threads)
    threads.close()
    return thread_id

def send_openai_message(discord_thread, user, content):
    thread_id = get_thread(discord_thread)
    message = openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user + ": " + content + " {Important! limit reply to 2000 characters. Less is better.}",
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    while run.status != "completed":
        keep_retrieving_run = openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        print(f"Run status: {keep_retrieving_run.status}")

        if keep_retrieving_run.status == "completed":
            print("\n")
            break

    reply = openai.beta.threads.messages.list(
        thread_id=thread_id
    )
    return str(reply.data[0].content[0].text.value)


@client.event
async def on_message(message):
    if message.author.bot or not message.content:
        return
    print(message.channel.type)
    if "thread" in str(message.channel.type):
        async with message.channel.typing():
            status = str("gpt-assistant is Typing...")
            await message.reply(send_openai_message(str(message.channel.id), str(message.author.display_name), str(message.content)))
    else:
        thread = await message.create_thread(name=str(message.content)[:20], auto_archive_duration=60)
        async with client.get_channel(int(thread.id)).typing():
            await client.get_channel(int(thread.id)).send(send_openai_message(str(client.get_channel(int(thread.id)).id), str(message.author), str(message.content)))

client.run(discord_token)
