import config
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from cryptography.fernet import Fernet
import base64
import hashlib

bot = Bot(token=config.TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form:
    mode = 'mode'
    message = 'message'
    key = 'key'

#Функция шифрования
def encrypt_message(message: str, key: str) -> str:
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message.decode()

#Функция дешифрования
def decrypt_message(encrypted_message: str, key: str) -> str:
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message.encode())
    return decrypted_message.decode()

#Функция генерации ключа
def generate_key(input_string: str) -> str:
    hash_object = hashlib.sha256(input_string.encode())
    key = base64.urlsafe_b64encode(hash_object.digest())
    return key.decode()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('Шифрование'), KeyboardButton('Дешифрование'))

@dp.message_handler(Command('start'))
async def start_cmd_handler(message: types.Message):
    await message.answer('''Привет! я бот для шифрования сообшений.
    Инструкция по пользованию:
    
    - Выбирите действие из меню ниже (Шифрование \ Дешифрование)
    
    - Введите сообщение
    
    - Введите ключ штфрования (Его должны знать вы и получатель)
    
    
    Выберите действие:''', reply_markup=keyboard)

@dp.message_handler(Text(equals='Шифрование'))
async def encrypt_cmd_handler(message: types.Message):
    await dp.current_state().set_state(Form.mode)
    await dp.current_state().update_data(mode='Шифрование')
    await message.answer('Введите сообщение для шифрования:')
    await dp.current_state().set_state(Form.message)

@dp.message_handler(Text(equals='Дешифрование'))
async def decrypt_cmd_handler(message: types.Message):
    await dp.current_state().set_state(Form.mode)
    await dp.current_state().update_data(mode='Дешифрование')
    await message.answer('Введите сообщение для дешифрования:')
    await dp.current_state().set_state(Form.message)

@dp.message_handler(state=Form.message)
async def get_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text
    await message.answer('Введите ключ для шифрования/дешифрования(его нужно записать и передать получателю. Лучше голосом, чтобы его не перехватили и не могли дешифровать сообщение):')
    await state.set_state(Form.key)

@dp.message_handler(state=Form.key)
async def process_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['key'] = message.text
        key = generate_key(data['key'])
        mode = data['mode']
        text_to_process = data['message']
        try:
            if mode == 'Шифрование':
                processed_text = encrypt_message(text_to_process, key)
                await message.answer(f'Зашифрованное сообщение: {processed_text}')
            elif mode == 'Дешифрование':
                processed_text = decrypt_message(text_to_process, key)
                await message.answer(f'Дешифрованное сообщение: {processed_text}')
        except Exception as e:
            error_message = (f'''Ошибка при обработке сообщения не верно введен текст либо не верный ключ. 
            Приверте вводимые данные и повторите попытку: {e}''')
            await message.answer(error_message)
    await state.finish()