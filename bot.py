import random
import asyncio
import nest_asyncio  # type: ignore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Разрешаем вложенные циклы событий
nest_asyncio.apply()

# Словарь для хранения очков игроков
player_scores = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in player_scores:
        player_scores[user_id] = 0  # Инициализируем счет игрока

    keyboard = [
        [InlineKeyboardButton("Играть", callback_data='play')],
        [InlineKeyboardButton("Мой счет", callback_data='score')],
        [InlineKeyboardButton("Другое", callback_data='other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Привет! Выберите действие:', reply_markup=reply_markup)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Кубик🎲", callback_data='play_dice')], 
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Выберите игру:", reply_markup=reply_markup)

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name  # Нужно для вывода имени в рейтинге

    # Сортировка игроков по счёту (от большего к меньшему)
    sorted_scores = sorted(player_scores.items(), key=lambda item: item[1], reverse=True)
    ranking = [f"{i+1}. {context.bot.get_chat(item[0]).first_name}" for i, item in enumerate(sorted_scores)][:5]  # Топ 5 игроков
    ranking_position = sorted_scores.index((user_id, player_scores[user_id])) + 1

    await query.edit_message_text(
        text=f"Рейтинг:\n{'\n'.join(ranking)}\n\nВы: {player_scores[user_id]} ({ranking_position} место)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]])
    )

async def other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Поддержать автора)\n2202206260918441 (сбербанк))",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]]))

async def dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id

    if query.data == 'play_dice': 
        keyboard = [
            [InlineKeyboardButton("Чет/Нечет", callback_data='even_odd')],
            [InlineKeyboardButton("Больше/Меньше", callback_data='greater_less')],  # Добавили кнопку "Больше/Меньше"
            [InlineKeyboardButton("Угадай число", callback_data='guess_number')],
            [InlineKeyboardButton("Сегменты", callback_data='segments')],
            [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Используем reply_to_message_id
        await query.edit_message_text(text="Выберите режим:", reply_markup=reply_markup) 

    elif query.data == 'stop':
        await query.message.reply_text(f"Жаль😔 напишите /start когда захотите продолжить \nТекущий счет: {player_scores[user_id]}")

    elif query.data == 'back_to_main_menu':
        await start(update, context)

    elif query.data == 'even_odd': 
        context.user_data['mode'] = 'even_odd'  # Сохраняем выбранный режим
        await bet_even_odd(update, context)

    elif query.data == 'greater_less':
        context.user_data['mode'] = 'greater_less'  # Сохраняем выбранный режим
        await bet_greater_less(update, context)

    elif query.data == 'guess_number':
        context.user_data['mode'] = 'guess_number'  # Сохраняем выбранный режим
        await guess_number_game(update, context)

    elif query.data == 'segments':  # Обрабатываем кнопку "Сегменты"
        context.user_data['mode'] = 'segments'  # Сохраняем выбранный режим
        await bet_segments(update, context)

    elif query.data in ['even', 'odd', 'greater', 'less']:
        await roll_dice(update, context)

async def bet_even_odd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Четное", callback_data='even')],
        [InlineKeyboardButton("Нечетное", callback_data='odd')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Сделайте ставку:", reply_markup=reply_markup)

    # Сохраняем режим в context.user_data
    context.user_data['mode'] = 'even_odd'

async def bet_greater_less(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Больше", callback_data='greater')],
        [InlineKeyboardButton("Меньше", callback_data='less')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Сделайте ставку:", reply_markup=reply_markup)

    # Сохраняем режим в context.user_data
    context.user_data['mode'] = 'greater_less'
    context.user_data['bet'] = query.data  # Сохраняем ставку в context.user_data

async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE, bet=None) -> None:  # Добавили bet
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    # Определяем результат
    result = ""

    # Бросаем кубик с анимацией (3 секунды) 
    await asyncio.sleep(1)
    dice_message = await query.message.reply_dice(emoji='🎲')  # Отправляем анимацию кубика
    await asyncio.sleep(3)  # Ждем окончания анимации

    roll = dice_message.dice.value  # Получаем значение брошенного кубика
    if context.user_data['mode'] == 'even_odd':  # Чет/Нечет
        result = "ПОБЕДА🏆" if roll % 2 == 0 else "ПРОИГРЫШ🎭"  # Исправлено условие четности
    elif context.user_data['mode'] == 'greater_less':  # Больше/Меньше

        if bet == 'greater':  # Больше
            result = "ПОБЕДА🏆" if roll > 3 else "ПРОИГРЫШ🎭"
        elif bet == 'less':  # Меньше
            result = "ПОБЕДА🏆" if roll < 4 else "ПРОИГРЫШ🎭"
    elif context.user_data['mode'] == 'segments':  # Сегменты
        if context.user_data['bet'] == 'lower' and roll in [1, 2]:
            result = "ПОБЕДА🏆"
        elif context.user_data['bet'] == 'middle' and roll in [3, 4]:
            result = "ПОБЕДА🏆"
        elif context.user_data['bet'] == 'higher' and roll in [5, 6]:
            result = "ПОБЕДА🏆"
        else:
            result = "ПРОИГРЫШ🎭"

    # Выводим результат с кнопками - используем reply_text
    keyboard = [
        [InlineKeyboardButton("Продолжить", callback_data='play_dice')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(f"🎲  Кубик выпал: {roll}. {result}", reply_markup=reply_markup)  #  Измененное сообщение

    # Обновляем счет игрока, если выиграл
    if result == "ПОБЕДА🏆":
        player_scores[user_id] += 1

    # Задержка в 1 секунду
    await asyncio.sleep(1)

async def guess_number_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("1", callback_data='1')],
        [InlineKeyboardButton("2", callback_data='2')],
        [InlineKeyboardButton("3", callback_data='3')],
        [InlineKeyboardButton("4", callback_data='4')],
        [InlineKeyboardButton("5", callback_data='5')],
        [InlineKeyboardButton("6", callback_data='6')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Выберите число от 1 до 6:", reply_markup=reply_markup)

async def guess_number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    guess = int(query.data)

    # Бросаем кубик 
    await asyncio.sleep(1)
    dice_message = await query.message.reply_dice(emoji='🎲')  # Отправляем анимацию кубика
    secret_number = dice_message.dice.value  # Получаем значение брошенного кубика
    await asyncio.sleep(3)  # Ждем окончания анимации

    result = ""
    if guess == secret_number:
        result = "ПОБЕДА🏆"
        player_scores[user_id] += 1
    else:
        result = "ПРОИГРЫШ🎭"

    # Выводим результат с кнопками - используем reply_text
    keyboard = [
        [InlineKeyboardButton("Продолжить", callback_data='play_dice')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(f"🎲  Кубик выпал: {secret_number}. {result}", reply_markup=reply_markup)

    # Задержка в 1 секунду
    await asyncio.sleep(1)

    await play(update, context)  # Возвращаемся к выбору режима игры

async def bet_segments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Низший сегмент (1-2)", callback_data='lower')],
        [InlineKeyboardButton("Средний сегмент (3-4)", callback_data='middle')],
        [InlineKeyboardButton("Высший сегмент (5-6)", callback_data='higher')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Сделайте ставку:", reply_markup=reply_markup)

    # Сохраняем режим в context.user_data
    context.user_data['mode'] = 'segments'
    context.user_data['bet'] = query.data  # Сохраняем ставку в context.user_data

async def segments_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # Бросаем кубик 
    await asyncio.sleep(1)
    dice_message = await query.message.reply_dice(emoji='🎲')  # Отправляем анимацию кубика
    roll = dice_message.dice.value  # Получаем значение брошенного кубика
    await asyncio.sleep(3)  # Ждем окончания анимации

    result = ""
    if context.user_data['bet'] == 'lower' and roll in [1, 2]:
        result = "ПОБЕДА🏆"
        player_scores[user_id] += 1
    elif context.user_data['bet'] == 'middle' and roll in [3, 4]:
        result = "ПОБЕДА🏆"
        player_scores[user_id] += 1
    elif context.user_data['bet'] == 'higher' and roll in [5, 6]:
        result = "ПОБЕДА🏆"
        player_scores[user_id] += 1
    else:
        result = "ПРОИГРЫШ🎭"

    # Выводим результат с кнопками - используем reply_text
    keyboard = [
        [InlineKeyboardButton("Продолжить", callback_data='continue')],
        [InlineKeyboardButton("Главное меню", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(f"🎲  Кубик выпал: {roll}. {result}", reply_markup=reply_markup)

    # Задержка в 1 секунду
    await asyncio.sleep(1)

    # Возвращаемся к выбору режима игры
    await play(update, context) 

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == 'play_dice':  
        await dice_game(update, context)  

    elif query.data == 'play':
        await play(update, context) 

    elif query.data == 'score':
        await score(update, context)

    elif query.data == 'other':
        await other(update, context)

    elif query.data == 'back_to_main_menu':
        await start(update, context)

    elif query.data == 'even_odd':  # Обрабатываем "Чет/Нечет"
        await bet_even_odd(update, context)

    elif query.data == 'greater_less':  # Обрабатываем "Больше/Меньше"
        await bet_greater_less(update, context)

    elif query.data in ['even', 'odd']:
        await roll_dice(update, context)  # Обработка кнопок "Четное" и "Нечетное"
    elif query.data in ['greater', 'less']:  # Обработка кнопок "Больше" и "Меньше"
        await roll_dice(update, context, query.data)  # Передаем ставку в roll_dice

    elif query.data == 'continue':
        if 'mode' in context.user_data:
            await dice_game(update, context)  # Вызываем dice_game для возврата к выбору режима игры

    elif query.data == 'guess_number':  # Обрабатываем кнопку "Угадай число"
        await guess_number_game(update, context)

    elif query.data in ['1', '2', '3', '4', '5', '6']:  # Обрабатываем кнопки выбора числа в "Угадай число"
        await guess_number_handler(update, context) 

    elif query.data == 'segments':  # Обрабатываем кнопку "Сегменты"
        await bet_segments(update, context)  # Вызываем bet_segments для "Сегменты"

async def main() -> None:
    application = ApplicationBuilder().token('7927429460:AAG-uicBpkJ4ayiSQ7_XW9wmmODjlikb2g0').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    await application.initialize()  # Инициализация приложения
    await application.run_polling()  # Запуск опроса

# Запуск приложения
if __name__ == '__main__':
    asyncio.run(main())