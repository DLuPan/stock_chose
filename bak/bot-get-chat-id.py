from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
from telegram.ext.filters import ALL
from telegram import Bot
from dotenv import load_dotenv
import os

# 加载 .env 文件中的变量
load_dotenv()

# 从环境变量中获取 Token
TOKEN = os.getenv("BOT_TOKEN")


# 定义处理函数
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    await update.message.reply_text(f"群组名称: {chat_title}\nChat ID: {chat_id}")
    print(f"群组名称: {chat_title}, Chat ID: {chat_id}")


def main():

    # 创建应用
    application = ApplicationBuilder().token(TOKEN).build()

    # 添加消息处理器
    application.add_handler(MessageHandler(ALL, get_chat_id))

    # 运行机器人
    application.run_polling()


if __name__ == "__main__":
    main()
