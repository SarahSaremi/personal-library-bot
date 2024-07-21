import os
import django
from django.db.models import Q
from telethon import TelegramClient, events
from telethon.sync import TelegramClient

from library_bot.books.models import Book

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookbot.settings')
django.setup()

API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
BOT_TOKEN = 'YOUR_BOT_TOKEN'

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def start(event):
    await event.respond('Welcome to the Book Manager Bot! Use /add to add a new book.')
    raise events.StopPropagation


@client.on(events.NewMessage(pattern='/add'))
async def add(event):
    await event.respond('Enter the book title:')
    client.add_event_handler(title, events.NewMessage(from_users=event.sender_id))


async def title(event):
    client.remove_event_handler(title)
    context = {'title': event.text}
    await event.respond('Enter the writer:')
    client.add_event_handler(writer, events.NewMessage(from_users=event.sender_id, incoming=True), context=context)


async def writer(event):
    context = event._event_handler.context
    context['writer'] = event.text
    client.remove_event_handler(writer)
    await event.respond('Enter the translator (if any, or type "None"):')
    client.add_event_handler(translator, events.NewMessage(from_users=event.sender_id, incoming=True), context=context)


async def translator(event):
    context = event._event_handler.context
    translator = event.text
    context['translator'] = translator if translator.lower() != 'none' else None
    client.remove_event_handler(translator)
    await event.respond('Enter the borrower:')
    client.add_event_handler(borrower, events.NewMessage(from_users=event.sender_id, incoming=True), context=context)


async def borrower(event):
    context = event._event_handler.context
    context['borrower'] = event.text
    client.remove_event_handler(borrower)

    title = context['title']
    writer = context['writer']
    existing_book = Book.objects.filter(title=title, writer=writer).first()

    if existing_book:
        await event.respond(
            f'The book "{title}" by {writer} already exists. Are you sure you want to add a duplicate? (yes/no)'
        )
        client.add_event_handler(confirm, events.NewMessage(from_users=event.sender_id, incoming=True), context=context)
    else:
        add_book(context)
        await event.respond('Book added successfully!')


async def confirm(event):
    context = event._event_handler.context
    client.remove_event_handler(confirm)

    if event.text.lower() == 'yes':
        add_book(context)
        await event.respond('Book added successfully!')
    else:
        await event.respond('Book not added.')


def add_book(book_data):
    new_book = Book(
        title=book_data['title'],
        writer=book_data['writer'],
        translator=book_data['translator'],
        borrower=book_data['borrower']
    )
    new_book.save()


@client.on(events.NewMessage(pattern='/search'))
async def search(event):
    query = event.text.split(maxsplit=1)[1] if len(event.text.split()) > 1 else ""
    results = Book.objects.filter(
        Q(title__icontains=query) |
        Q(writer__icontains=query) |
        Q(translator__icontains=query)
    )

    if results:
        response = 'Found the following books:\n'
        for book in results:
            response += f'Title: {book.title}, Writer: {book.writer}, Translator: {book.translator}, Borrower: {book.borrower}\n'
    else:
        response = 'No books found.'

    await event.respond(response)


def main():
    client.add_event_handler(start, events.NewMessage(pattern='/start'))
    print('Bot is running...')
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
