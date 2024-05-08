import asyncio
import os
import sys
import time
import redis
from pyrogram import Client, idle
from pyrogram.enums import ParseMode, ChatType, ChatMemberStatus
from pyrogram.handlers import MessageHandler, ChatMemberUpdatedHandler
from pyrogram.session.session import Session
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from g4f.client import Client as chatgpt


# Genera sessione pyro
async def pyro(token):
    Session.notice_displayed = True

    API_HASH = ''
    API_ID = ''

    bot_id = str(token).split(':')[0]
    app = Client(
        'sessioni/session_bot' + str(bot_id),
        api_hash=API_HASH,
        api_id=API_ID,
        bot_token=token,
        workers=20,
        sleep_threshold=30
    )
    return app

async def wrap_send_del(bot: Client, chatid: int, text: str):
    delete=await db.getLastmsg(chatid)
    delete=delete[0]
    if int(delete) != 0:
        try:
            await bot.delete_messages(chatid, int(delete))
        except Exception as e:
            print(str(e))
    try:
        send = await bot.send_message(chatid, text)
        await db.updateLastmsg(send.id, chatid)
    except Exception as e:
        print("EXC in wrap_send_del:", str(e))


async def chat_handler(bot, update):
    old_member = update.old_chat_member
    new_member = update.new_chat_member
    if old_member and not old_member.user.id == bot_id: return
    if new_member and not new_member.user.id == bot_id: return 
    if update.chat.type == ChatType.CHANNEL:
        try:
            await bot.leave_chat(chat_id=update.chat.id)
        except Exception as e:
            print(str(e))
        return
    if (not update.old_chat_member or update.old_chat_member.status == ChatMemberStatus.BANNED): # controllo se l'evento è specificamente di aggiunta
        members=await bot.get_chat_members_count(update.chat.id)
        if members<50:
            await bot.send_message(update.chat.id, "Mi dispiace, il bot è abilitato solamente per gruppi con almeno 50 utenti, riaggiungilo quando avrai raggiunto quella soglia, per qualsiasi chiarimento @spidernukleo")
            await bot.leave_chat(chat_id=update.chat.id)
        elif update.chat.type == ChatType.GROUP:
            await bot.send_message(update.chat.id, "Mi dispiace, il bot è abilitato solamente per SUPERGRUPPI, riaggiungilo quando avrai reso questo gruppo un supergruppo, per qualsiasi chiarimento @spidernukleo")
            await bot.leave_chat(chat_id=update.chat.id)
        else:
            await bot.send_message(update.chat.id, "Grazie per aver aggiunto Intelligenza Artificale!\n\nComandi:\n<code>/gpt prompt</code> per generare testo con gpt 3.5\n<code>/img prompt</code> per generare un immagine con gemini\n\nPer qualsiasi problema @spidernukleo")
        
            
    return

async def bot_handler(bot, message):
    tipo = message.chat.type
    if message.media or message.service: return
    text = str(message.text)
    if text == '/start' or text == '/start@intelligenzatoolartificialebot':
        chatid = message.chat.id
        if tipo==ChatType.PRIVATE:
            text="👁 Benvenuto nel tuo bot di Intelligenza Artificale!\n\nComandi:\n<code>/gpt prompt</code> per generare testo con gpt 3.5\n<code>/img prompt</code> per generare un immagine con gemini\n\nPremi il bottone qua sotto per aggiungere il bot ai tuoi gruppi ora!\n\nCreato da @spidernukleo"
            await bot.send_message(chatid, text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Aggiungimi ora!",url="https://t.me/intelligenzatoolartificialebot?startgroup")]]))
        else:
            await bot.send_message(chatid, "Grazie per aver aggiunto Intelligenza Artificale!\n\nComandi:\n<code>/gpt prompt</code> per generare testo con gpt 3.5\n<code>/img prompt</code> per generare un immagine con gemini\n\nPer qualsiasi problema @spidernukleo")


    elif text.startswith("/gpt"):
        if len(message.text.split()) > 1:
            prompt= ' '.join(message.text.split()[1:]) 
        else:
            return

        last_time=redis.get(message.from_user.id)
        if last_time:
            elapsed_time = time.time() - float(last_time)
            if elapsed_time<10: return
        redis.set(message.from_user.id, time.time())


        reply = await message.reply("📝 Generazione testo...", quote=True)
        try:
            response = gpt.chat.completions.create(messages=[{"role": "user","content": "la risposta deve essere in italiano.\n"+prompt}], model="gpt-3.5-turbo")
            answer = "**Input:** `" + prompt + "`\n\n**Risultato :** " + response.choices[0].message.content
            await reply.edit(answer)
        except Exception as e:
            await bot.send_message("spidernukleo", f"Errore: {str(e)} in {message.chat.title} : {message.chat.id}")
            await message.reply(f"Errore {message.chat.title} : {message.chat.id}, contattare @spidernukleo")

    elif text.startswith("/img"):

        if len(message.text.split()) > 1:
            prompt= ' '.join(message.text.split()[1:]) 
        else:
            return

        last_time=redis.get(message.from_user.id)
        if last_time:
            elapsed_time = time.time() - float(last_time)
            if elapsed_time<3: return
        redis.set(message.from_user.id, time.time())

        await message.reply("Comando temporaneamente offline", quote=True)
        '''
        reply = await message.reply("📝 Generazione immagine...", quote=True)

        response = await gpt.images.generate(model="dall-e-3",prompt=prompt)

        try:
            await message.reply_photo(response.data[0].url,caption="**Risultato per** "+prompt)
        except Exception as e:
            await bot.send_message("spidernukleo", f"Errore: {str(e)} in {message.chat.title} : {message.chat.id}")
            await message.reply(f"Errore {message.chat.title} : {message.chat.id}, contattare @spidernukleo")
        '''


async def main(bot_id):
    print(f'Genero sessione [{bot_id}] > ', end='')
    SESSION = await pyro(token=TOKEN)
    HANDLERS = {
        'msg': MessageHandler(bot_handler),
        'chat': ChatMemberUpdatedHandler(chat_handler)
    }
    SESSION.add_handler(HANDLERS['msg'])
    SESSION.add_handler(HANDLERS['chat'])


    print('avvio > ', end='')
    await SESSION.start()

    print('avviati!')
    await idle()

    print('Stopping > ', end='')
    await SESSION.stop()

    loop.stop()
    print('stopped!\n')
    exit()


if __name__ == '__main__':
    TOKEN = ''
    bot_id = int(TOKEN.split(':')[0])
    loop = asyncio.get_event_loop()
    gpt = chatgpt()
    redis = redis.Redis(host='localhost', port=6379, db=3)
    loop.run_until_complete(main(bot_id))
    exit()
