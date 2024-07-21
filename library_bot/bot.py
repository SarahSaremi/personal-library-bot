import os
import django
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup
from books.models import Book

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookbot.settings')
django.setup()

TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Conversation states
TITLE, WRITER, TRANSLATOR, BORROWER, CONFIRM = range(5)


def start(update, context):
    update.message.reply_text('Welcome to the Book Manager Bot! Use /add to add a new book.')
    return


def add(update, context):
    update.message.reply_text('Enter the book title:')
    return TITLE


def title(update, context):
    context.user_data['title'] = update.message.text
    update.message.reply_text('Enter the writer:')
    return WRITER


def writer(update, context):
    context.user_data['writer'] = update.message.text
    update.message.reply_text('Enter the translator (if any, or type "None"):')
    return TRANSLATOR


def translator(update, context):
    translator = update.message.text
    context.user_data['translator'] = translator if translator.lower() != 'none' else None
    update.message.reply_text('Enter the borrower:')
    return BORROWER


def borrower(update, context):
    context.user_data['borrower'] = update.message.text

    # Check for duplicate
    title = context.user_data['title']
    writer = context.user_data['writer']
    existing_book = Book.objects.filter(title=title, writer=writer).first()

    if existing_book:
        update.message.reply_text(
            f'The book "{title}" by {writer} already exists. Are you sure you want to add a duplicate? (yes/no)',
            reply_markup=ReplyKeyboardMarkup([['yes', 'no']], one_time_keyboard=True)
        )
        return CONFIRM
    else:
        add_book(context.user_data)
        update.message.reply_text('Book added successfully!')
        return ConversationHandler.END


def confirm(update, context):
    if update.message.text.lower() == 'yes':
        add_book(context.user_data)
        update.message.reply_text('Book added successfully!')
    else:
        update.message.reply_text('Book not added.')
    return ConversationHandler.END


def add_book(book_data):
    new_book = Book(
        title=book_data['title'],
        writer=book_data['writer'],
        translator=book_data['translator'],
        borrower=book_data['borrower']
    )
    new_book.save()


def cancel(update, context):
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END


def search(update, context):
    query = ' '.join(context.args)
    results = Book.objects.filter(
        models.Q(title__icontains=query) |
        models.Q(writer__icontains=query) |
        models.Q(translator__icontains=query)
    )

    if results:
        response = 'Found the following books:\n'
        for book in results:
            response += f'Title: {book.title}, Writer: {book.writer}, Translator: {book.translator}, Borrower: {book.borrower}\n'
    else:
        response = 'No books found.'

    update.message.reply_text(response)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            TITLE: [MessageHandler(Filters.text & ~Filters.command, title)],
            WRITER: [MessageHandler(Filters.text & ~Filters.command, writer)],
            TRANSLATOR: [MessageHandler(Filters.text & ~Filters.command, translator)],
            BORROWER: [MessageHandler(Filters.text & ~Filters.command, borrower)],
            CONFIRM: [MessageHandler(Filters.regex('^(yes|no)$'), confirm)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('search', search))
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
