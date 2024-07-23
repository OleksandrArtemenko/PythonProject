import os

import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  # Updated import for ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler


class NewsBot:
    def __init__(self):
        load_dotenv()
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.NEWS_API_KEY = os.getenv('NEWS_API_KEY')
        self.application = Application.builder().token(self.TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()

    def fetch_news(self, query, page=1):
        url = f'https://newsapi.org/v2/everything?q={query}&apiKey={self.NEWS_API_KEY}&page={page}&pageSize=5'
        response = requests.get(url)
        return response.json().get('articles', [])

    async def start(self, update: Update, context: CallbackContext) -> None:
        await update.message.reply_text('Hi! Use /news <keyword> to get the latest news.')

    def format_article(self, article):
        return f"*{article['title']}*\n_{article['source']['name']}_\n\n{article['description']}\n[Read more]({article['url']})"

    async def news(self, update: Update, context: CallbackContext) -> None:
        query = ' '.join(context.args)
        if not query:
            await update.message.reply_text('Please provide a keyword.')
            return

        articles = self.fetch_news(query)
        if not articles:
            await update.message.reply_text('No articles found.')
            return

        context.user_data['query'] = query
        context.user_data['page'] = 1

        for article in articles:
            await update.message.reply_text(self.format_article(article), parse_mode=ParseMode.MARKDOWN)

        keyboard = [
            [InlineKeyboardButton("Next 5 News", callback_data='next_news')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Show more news?", reply_markup=reply_markup)

    async def next_news(self, update: Update, context: CallbackContext) -> None:
        query = context.user_data.get('query')
        page = context.user_data.get('page', 1) + 1
        context.user_data['page'] = page

        articles = self.fetch_news(query, page)
        if not articles:
            await update.callback_query.answer("No more articles found.")
            return

        for article in articles:
            await update.callback_query.message.reply_text(self.format_article(article), parse_mode=ParseMode.MARKDOWN)

        keyboard = [
            [InlineKeyboardButton("Next 5 News", callback_data='next_news')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Show more news?", reply_markup=reply_markup)
        await update.callback_query.answer()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("news", self.news))
        self.application.add_handler(CallbackQueryHandler(self.next_news, pattern='next_news'))

    def run(self):
        self.application.run_polling()


if __name__ == '__main__':
    bot = NewsBot()
    bot.run()
