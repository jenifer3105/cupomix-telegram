
import os
import re
import json
import html
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
        publicados = set(
            json.loads(ARQUIVO.read_text(encoding="utf-8"))
        )
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
        r"\b([A-Z0-9]{7,20})\s*:\s*R\$\s*\d+",
        r"\b([A-Z0-9]{7,20})\b",
    ]

    ignorar = {
        "SHOPEE", "CUPOM", "CODIGO", "CÓDIGO",
        "DESCONTO", "RESGATE", "CARRINHO", "OFERTA"
    }

    for padrao in padroes:
        for resultado in re.finditer(padrao, texto, re.IGNORECASE):
            codigo = resultado.group(1).upper()
            if codigo not in ignorar:
                return codigo

    return None


async def main():
    bot = Bot(token=BOT_TOKEN)
    client = TelegramClient("sessao_cupons", API_ID, API_HASH)

    await client.start()

    @client.on(events.NewMessage(chats=CANAIS))
    async def receber(event):
        texto = event.raw_text or ""

        if not re.search(
            r"shopee|s\.shopee\.com|shopee\.com",
            texto,
            re.IGNORECASE
        ):
            return

        codigo = extrair_codigo(texto)

        if not codigo or codigo in publicados:
            return

        # Extrai os links da publicação original.
        links = re.findall(r"https?://\S+", texto)
        links = [link.rstrip(".,!)\]}") for link in links]

        link_resgate = next(
            (
                link for link in links
                if "shopee" in link.lower()
                and not re.search(r"carrinho|cart", link, re.I)
            ),
            None
        )

        link_carrinho = next(
            (
                link for link in links
                if "shopee" in link.lower()
                and re.search(r"carrinho|cart", link, re.I)
            ),
            None
        )

        # Mantém o link original da publicação como alternativa.
        username = getattr(event.chat, "username", None)
        link_original = (
            f"https://t.me/{username}/{event.message.id}"
            if username else ""
        )

        if not link_resgate:
            link_resgate = link_original

        # Procura valor de desconto e compra mínima.
        desconto = re.search(
            r"R\$\s*\d+(?:[,.]\d+)?\s*OFF"
            r"(?:\s+em\s+R\$\s*\d+(?:[,.]\d+)?)?",
            texto,
            re.IGNORECASE
        )

        valor = desconto.group(0) if desconto else "Cupom disponível"

        mensagem = (
            "🎟️ <b>CUPOM SHOPEE</b> 🎟️\n\n"
            f"💸 <b>{html.escape(valor)}</b>\n\n"
            f"🏷️ <b>CÓDIGO:</b> <code>{html.escape(codigo)}</code>\n\n"
        )

        if link_resgate:
            mensagem += (
                f'✅ <b>Resgate aqui:</b>\n'
                f'<a href="{html.escape(link_resgate, quote=True)}">'
                f'Abrir cupom Shopee</a>\n\n'
            )

        if link_carrinho:
            mensagem += (
                f'🛒 <b>Carrinho:</b>\n'
                f'<a href="{html.escape(link_carrinho, quote=True)}">'
                f'Abrir carrinho</a>\n\n'
            )

        if link_original:
            mensagem += (
                f'🔎 <a href="{html.escape(link_original, quote=True)}">'
                f'Ver publicação original</a>'
            )

        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=mensagem,
                parse_mode="HTML",
                disable_web_page_preview=True
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
