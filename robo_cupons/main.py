
import os
import re
import json
import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from telegram import Bot

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CANAIS = [
    "cuponsvoltando",
    "fadadoscupons",
    "afiliadosshopeebroficial",
]

ARQUIVO = Path("cupons.json")
publicados = set()

if ARQUIVO.exists():
    try:
        publicados = set(json.loads(ARQUIVO.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        publicados = set()

def salvar():
    ARQUIVO.write_text(
        json.dumps(sorted(publicados), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def extrair_codigo(texto):
    padroes = [
        r"(?:código|cupom|code)\s*[:\-]?\s*([A-Z0-9]{5,25})",
        r"\b([A-Z0-9]{5,20})\s*:\s*R\$\s*\d+",
    ]
    for padrao in padroes:
        resultado = re.search(padrao, texto, re.IGNORECASE)
        if resultado:
            codigo = resultado.group(1).upper()
            if codigo not in {"SHOPEE", "CUPOM", "CÓDIGO"}:
                return codigo
    return None

async def main():
    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient("sessao_cupons", API_ID, API_HASH)

    await client.start()

    @client.on(events.NewMessage(chats=CANAIS))
    async def receber(event):
        texto = event.raw_text or ""
        link = f"https://t.me/{event.chat.username}/{event.message.id}"

        if not re.search(r"shopee|s\.shopee\.com\.br", texto, re.IGNORECASE):
            return

        codigo = extrair_codigo(texto)
        if not codigo or codigo in publicados:
            return

        mensagem = (
            "🎟️ <b>CUPOM SHOPEE</b>\n\n"
            f"{texto[:2500]}\n\n"
            f'🔗 <a href="{link}">Ver publicação original</a>'
        )

        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=mensagem,
                parse_mode="HTML"
            )
            publicados.add(codigo)
            salvar()
            print(f"Cupom publicado: {codigo}")
        except Exception as erro:
            print(f"Erro ao publicar {codigo}: {erro}")

    print("Robô de cupons iniciado.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
