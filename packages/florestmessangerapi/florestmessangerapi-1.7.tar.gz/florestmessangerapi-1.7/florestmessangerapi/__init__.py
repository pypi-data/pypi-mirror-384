"""Библиотека для взаимодействия с [API FlorestMessanger для ботов](https://florestmsgs-florestdev4185.amvera.io/api_docs)!"""
import requests, time
from typing import Any, Callable
from colorama import Fore, init
import asyncio, aiohttp
from html import escape
from json import dumps
import json
from typing import Union, Dict, Any

init()

class CallBack:
    def __init__(self, data: Dict[str, Any]):
        """Инициализация объекта CallBack на основе данных о нажатии кнопки.
        
        Args:
            data (Dict[str, Any]): Словарь с данными о нажатии кнопки, содержащий поля
                username (str), message_id (int), callback_data (str или dict), timestamp (str).
        """
        self.data = data
        # Десериализация callback_data, если это JSON-строка
        self._callback_data = data.get('callback_data')
        try:
            self._callback_data = json.loads(self._callback_data)
        except (json.JSONDecodeError, TypeError):
            pass  # Оставляем как строку, если не JSON

    @property
    def username(self) -> str:
        """Имя пользователя, который нажал на кнопку."""
        return self.data.get('username', '')

    @property
    def message_id(self) -> int:
        """ID сообщения, связанного с кнопкой."""
        return self.data.get('message_id', 0)

    @property
    def callback_data(self) -> Union[str, Dict[str, Any]]:
        """Данные кнопки (строка или словарь, если callback_data был JSON)."""
        return self._callback_data

    @property
    def timestamp(self) -> str:
        """Время нажатия кнопки."""
        return self.data.get('timestamp', '')

class Button:
    def __init__(self, name: str, data: str):
        """Класс для создания кнопки.
        
        Args:
            name (str): Заголовок кнопки.
            data (str): Если строка, то проверяется на URL (http:// или https://) для кнопки-ссылки,
                              иначе считается callback. Если словарь, используется как есть для кнопки.
        
        Returns:
            dict: Словарь с полями 'name' и либо 'url', либо 'callback_data', либо содержимым словаря data.
        
        Note:
            Для обработки callback-кнопок не забудьте указать handler для этого!
        """
        if not name or (isinstance(data, str) and not data):
            raise ValueError("name и data не могут быть пустыми")

        if isinstance(data, str):
            # Если data — строка, проверяем, является ли она URL
            self.type_ = 'url' if data.startswith(('http://', 'https://')) else 'callback_data'
            self.data = {"text": escape(name), self.type_: escape(data)}
        else:
            raise TypeError("data должен быть строкой.")

class Message:
    def __init__(self, data: dict[str, Any]):
        self.data = data
    @property
    def type_msg(self) -> str:
        """Тип сообщения. (text/другие)"""
        return self.data.get("type")
    @property
    def username(self) -> str:
        """Ник автора сообщения."""
        return self.data.get("username")
    @property
    def content(self) -> str:
        """Содержание сообщения. Если сообщение текстовое - его текстовое содержание, если это файл/гс - прямая ссылка на него."""
        return self.data.get("content")
    @property
    def mime_type(self) -> str:
        """Тип медиа. Если текстовое сообщение - равняется None."""
        return self.data.get("mime_type")
    @property
    def id(self):
        """ID сообщения."""
        if self.data.get("id"):
            return int(self.data.get("id"))
    @property
    def is_admin(self):
        """Является ли человек администратором в чате."""
        if not self.data.get('is_admin'):
            return False
        else:
            return bool(self.data.get('is_admin'))
    @property
    def is_bot(self):
        """Является ли пользователь ботом."""
        if not self.data.get('is_bot'):
            return False
        else:
            return bool(self.data.get('is_bot'))
    @property
    def url_ava(self):
        """Ссылка на аватарку пользователя."""
        url_builder = self.data.get('avatar_url', f'/avatar/{self.username}')
        return f'https://florestmsgs-florestdev4185.amvera.io{url_builder}'
    def download_ava(self):
        """Вернет аватарку пользователя в bytes."""
        try:
            return requests.get(self.url_ava).content
        except:
            return
    @property
    def reply_to(self):
        """Возвращает ID сообщения, на которое был сделан ответ со стороны пользователя.\nNone, если сообщение не является ответным на чужое."""
        if self.data.get("reply_to"):
            return int(self.data.get('reply_to'))
    @property
    def buttons(self) -> list[Button]:
        """Возвращает список из кнопок, если они есть в сообщении."""
        btns_ = self.data.get('buttons', [])
        buttons: list[Button] = []
        for _ in btns_:
            if _.get('url'):
                buttons.append(Button(_.get("name"), _.get("url")))
            else:
                buttons.append(Button(_.get("name"), _.get('callback_data')))    
        return buttons

class Post:
    def __init__(self, post: dict[str, str]):
        self.post = post
    @property
    def title(self):
        """Заголовок поста."""
        return self.post.get('title')
    @property
    def description(self):
        """Описание поста."""
        return self.post.get("desc")
    @property
    def url(self):
        """Ссылка на пост."""
        return self.post.get("url")
    @property
    def author(self):
        """Ник автора поста."""
        return self.post.get('author')
    
class User:
    def __init__(self, data: str):
        self.data = data
    @property
    def username(self) -> str:
        """Ник пользователя."""
        return self.data
    
class Bot:
    def __init__(self, token: str, username: str, prefix: str = 'test!', proxies: dict[str, str] = None, raise_on_status_code: bool = False):
        """Класс для взаимодействия с ботами FlorestMessanger. Документация: https://florestmsgs-florestdev4185.amvera.io/api_docs\ntoken: токен бота. Создать бота и получить токен: https://florestmsgs-florestdev4185.amvera.io/your_bots\nusername: ник бота, чтобы он не реагировал на свои же сообщения.\nprefix: префикс команд. К примеру, `!`\nproxies: прокси для запросов. Необязательно.\nraise_on_status_code: производить ошибку при получении HTTP кода типов 400, 500, 401 и др. Хорошо для debug."""
        self.token = token
        self.proxies = proxies
        self.raise_on_status_code = raise_on_status_code
        self.username = username
        start = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_messages", headers={"X-Bot-Token":self.token}, proxies=self.proxies)
        start_ = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_clicks", headers={"X-Bot-Token":self.token}, proxies=self.proxies)
        if start.status_code != 200:
            if self.raise_on_status_code:
                print(f'{Fore.RED}Fucking exception! Stopping the polling..')
                raise Exception(f"ОШИБКА! КОД: {start.status_code}. JSON: {start.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
        self.start_messages = start.json().get("messages")
        self.start_clicks = start_.json().get('clicks')
        self.command_handlers = []
        self.callback_handler_set = None
        self.prefix = prefix
    def add_command(self, name: str) -> Callable:
        """Декоратор для добавления команды.
        Пример: @bot.add_command('hello') def func(message): ..."""
        def decorator(func: Callable[[Message], None]):
            self.command_handlers.append({'name': self.prefix + name, 'func': func})
            return func
        return decorator

    def set_callback_handler(self) -> Callable:
        """Декоратор. Чтобы сделать интерфейс для обработки нажатий на кнопки вашего бота.\nПример: @bot.set_callback_handler() def func(callback: CallBack): ..."""
        def decorator(func: Callable[[CallBack], None]):
            self.callback_handler_set = func
            return func
        return decorator

    def get_users(self) -> list[User]:
        """Функция для получения списка пользователей на данный момент."""
        r = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_users", proxies=self.proxies, headers={"X-Bot-Token":self.token})
        if r.status_code != 200:
            if self.raise_on_status_code:
                raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
            else:
                return []
        else:
            _ = []
            for u in r.json()["usernames"]:
                _.append(User(u))
            return _
    def send_message(self, text: str, buttons: list[Button] = []) -> bool:
        """Отправка текстового сообщения.\ntext: текст сообщения."""
        formatted_btns = []
        for button in buttons:
            formatted_btns.append(button.data)
        r = requests.post("https://florestmsgs-florestdev4185.amvera.io/api/bot/send_message", params={"content":text, "buttons":dumps(formatted_btns)}, proxies=self.proxies, headers={"X-Bot-Token":self.token})
        if r.status_code != 200:
            if self.raise_on_status_code:
                raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
            else:
                return False
        else:
            return True
    def send_media(self, media: Any, buttons: list[Button] = []) -> str:
        """Отправка медиа в чат любого типа. Видео, фото, файлы любых разрешений до 500 МБ.\nmedia: base64/bytes/buffer (к примеру, `open()`)\nВозвращает ссылку на отправленное медиа.\nРабота кнопок не гарантируется."""
        formatted_btns = []
        for button in buttons:
            formatted_btns.append(button.data)
        r = requests.post("https://florestmsgs-florestdev4185.amvera.io/api/bot/send_media", headers={"X-Bot-Token":self.token}, files={"file":media}, params={"buttons":dumps(formatted_btns)}, proxies=self.proxies)
        if r.status_code != 200:
            if self.raise_on_status_code:
                raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
            else:
                return False
        else:
            return r.json().get("url")
    def send_dm(self, username: str, content: str, buttons: list[Button] = None) -> bool:
        """Отправка личных сообщений пользователям для передачи чувствительных данных.\nusername: ник пользователя для отправки ЛС.\ncontent: что ему над написать?\n`True` при успешной отправке. `False` при отсутствии пользователя в сети, или при неправильном токене."""
        formatted_btns = []
        for button in buttons:
            formatted_btns.append(button.data)
        r = requests.post("https://florestmsgs-florestdev4185.amvera.io/api/bot/send_dm", params={"username":username, "content":content, 'buttons':dumps(formatted_btns)}, proxies=self.proxies, headers={"X-Bot-Token":self.token})
        if r.status_code != 200:
            if self.raise_on_status_code:
                raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
            else:
                return False
        else:
            return True
    def send_reply(self, message, content: str, buttons: list[Button] = []) -> bool:
        """Функция для ответа на чужое сообщение в мессенджере.\nmessage: экземпляр класса "Message", или ID сообщения (int).\ncontent: сообщение; как надо ответить на запрос.\nВозвращает True/False."""
        formatted_btns = []
        for button in buttons:
            formatted_btns.append(button.data)
        if isinstance(message, int):
            r = requests.post("https://florestmsgs-florestdev4185.amvera.io/api/bot/send_reply", params={"reply_to":message, "content":content, 'buttons':dumps(formatted_btns)}, proxies=self.proxies, headers={"X-Bot-Token":self.token})
            if r.status_code != 200:
                if self.raise_on_status_code:
                    raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                else:
                    return False
            else:
                return True
        elif isinstance(message, Message):
            r = requests.post("https://florestmsgs-florestdev4185.amvera.io/api/bot/send_reply", params={"reply_to":message.id, "content":content}, proxies=self.proxies, headers={"X-Bot-Token":self.token})
            if r.status_code != 200:
                if self.raise_on_status_code:
                    raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                else:
                    return False
            else:
                return True
        else:
            raise Exception(f'Неизвестный тип данных в аргументе message. Только класс Message и int!')
    def get_blogs(self) -> list[Post]:
        """Список постов с `/blogs`."""
        r = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_blogs", headers={"X-Bot-Token":self.token}, proxies=self.proxies)
        if r.status_code != 200:
            if self.raise_on_status_code:
                raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
            else:
                return []
        else:
            posts = []
            for i in r.json().get("blogs"):
                posts.append(Post(i))
            return posts
    def get_message(self, id_msg: int):
        """Получить сообщение по ID.\nid_msg: ID сообщения.\nВозвращает Message/None, или ошибку, если включен raise_on_status_code."""
        r = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_message", headers={"X-Bot-Token":self.token}, proxies=self.proxies, params={"id":id_msg})
        if r.status_code != 200:
            if self.raise_on_status_code:
                raise Exception(f"ОШИБКА! КОД: {r.status_code}. JSON: {r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
            else:
                return None
        else:
            return Message(r.json().get('message'))
    def run(self):
        """Start the bot's polling loop for messages and button clicks."""
        print(f'{Fore.YELLOW}STARTING OF POLLING FROM FLORESTMESSANGER\'S API!')
        while True:
            try:
                # Poll for new messages
                msg_req = requests.get(
                    "https://florestmsgs-florestdev4185.amvera.io/api/bot/get_messages",
                    headers={"X-Bot-Token": self.token},
                    proxies=self.proxies
                )
                if msg_req.status_code != 200:
                    if self.raise_on_status_code:
                        print(f'{Fore.RED}Fucking exception! Stopping the polling..')
                        raise Exception(f"ОШИБКА! КОД: {msg_req.status_code}. JSON: {msg_req.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                    time.sleep(1)
                    continue

                # Poll for new clicks
                click_req = requests.get(
                    "https://florestmsgs-florestdev4185.amvera.io/api/bot/get_clicks",
                    headers={"X-Bot-Token": self.token},
                    proxies=self.proxies
                )
                if click_req.status_code != 200:
                    if self.raise_on_status_code:
                        print(f'{Fore.RED}Fucking exception in click polling! Stopping the polling..')
                        raise Exception(f"ОШИБКА! КОД: {click_req.status_code}. JSON: {click_req.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                    time.sleep(1)
                    continue

                # Process new messages
                messages = msg_req.json().get("messages", [])
                for msg in messages:
                    if msg in self.start_messages:
                        continue
                    if msg.get("username") != self.username:
                        for handler in self.command_handlers:
                            if msg.get("content") and msg.get("content").startswith(handler.get('name')):
                                handler["func"](Message(msg))
                    self.start_messages.append(msg)

                # Process new clicks
                clicks = click_req.json().get("clicks", [])
                for click in clicks:
                    if click in self.start_clicks:
                        continue
                    if self.callback_handler_set:
                        callback = CallBack(click)
                        self.callback_handler_set(callback)
                    self.start_clicks.append(click)

                time.sleep(1)

            except requests.exceptions.RequestException as e:
                if self.raise_on_status_code:
                    print(f'{Fore.RED}Network error during polling: {e}')
                    raise
                time.sleep(5)  # Longer delay on network errors
                continue

class AsyncBot:
    def __init__(self, token: str, username: str, prefix: str = 'test!', proxies: dict[str, str] = None, raise_on_status_code: bool = False):
        """Класс для взаимодействия с ботами FlorestMessanger. Документация: https://florestmsgs-florestdev4185.amvera.io/api_docs\ntoken: токен бота. Создать бота и получить токен: https://florestmsgs-florestdev4185.amvera.io/your_bots\nusername: ник бота, чтобы он не реагировал на свои же сообщения.\nprefix: префикс команд. К примеру, `!`\nproxies: прокси для запросов. Необязательно.\nraise_on_status_code: производить ошибку при получении HTTP кода типов 400, 500, 401 и др. Хорошо для debug."""
        self.token = token
        self.proxies = proxies
        self.raise_on_status_code = raise_on_status_code
        self.username = username
        start = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_messages", headers={"X-Bot-Token":self.token}, proxies=self.proxies)
        if start.status_code != 200:
            if self.raise_on_status_code:
                print(f'{Fore.RED}Fucking exception! Stopping the polling..')
                raise Exception(f"ОШИБКА! КОД: {start.status_code}. JSON: {start.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
        self.start_messages = start.json().get("messages")
        self.command_handlers = []
        self.callback_handler_set = None
        start_ = requests.get("https://florestmsgs-florestdev4185.amvera.io/api/bot/get_clicks", headers={"X-Bot-Token":self.token}, proxies=self.proxies)
        self.start_clicks = start_.json().get('clicks')
        self.prefix = prefix
    def add_command(self, name: str) -> Callable:
        """Декоратор для добавления команды.
        Пример: @bot.add_command('hello') def func(message): ..."""
        def decorator(func: Callable[[Message], None]):
            self.command_handlers.append({'name': self.prefix + name, 'func': func})
            return func
        return decorator
    def set_callback_handler(self) -> Callable:
        """Декоратор. Чтобы сделать интерфейс для обработки нажатий на кнопки вашего бота.\nПример: @bot.set_callback_handler() def func(callback: CallBack): ..."""
        def decorator(func: Callable[[CallBack], None]):
            self.callback_handler_set = func
            return func
        return decorator
    async def get_users(self) -> list[User]:
        """Асинхронная функция для получения списка пользователей."""
        url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/get_users"
        headers = {"X-Bot-Token": self.token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, proxy=self.proxies, headers=headers) as r:
                    if r.status != 200:
                        if self.raise_on_status_code:
                            raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                        else:
                            return []
                    else:
                        data = await r.json()
                        users = [User(u) for u in data["usernames"]]
                        return users
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента aiohttp: {e}")
            return []

    async def send_message(self, text: str, buttons: list[Button] = []) -> bool:
        """Асинхронная отправка текстового сообщения."""
        url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/send_message"
        formatted_buttons = []
        for button in buttons:
            formatted_buttons.append(button.data)
        params = {"content": text, 'buttons':dumps(formatted_buttons)}
        headers = {"X-Bot-Token": self.token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, proxy=self.proxies, headers=headers) as r:
                    if r.status != 200:
                        if self.raise_on_status_code:
                            raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                        else:
                            return False
                    else:
                        return True
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента aiohttp: {e}")
            return False


    async def send_media(self, media: Any, buttons: list[Button] = []) -> str:
        """Асинхронная отправка медиа в чат любого типа.\nВозвращает ссылку на отправленное медиа."""
        url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/send_media"
        formatted_buttons = []
        for button in buttons:
            formatted_buttons.append(button.data)
        headers = {"X-Bot-Token": self.token}


        try:
            async with aiohttp.ClientSession() as session:
                 data = aiohttp.FormData()
                 data.add_field('file', media)
                 async with session.post(url, headers=headers, data=data, proxy=self.proxies) as r:
                    if r.status != 200:
                        if self.raise_on_status_code:
                            raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                        else:
                            return False
                    else:
                        j = await r.json()
                        return j.get("url")
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента aiohttp: {e}")
            return False
    
    async def send_dm(self, username: str, content: str, buttons: list[Button] = []) -> bool:
        """Отправка личных сообщений пользователям для передачи чувствительных данных.\nusername: ник пользователя для отправки ЛС.\ncontent: что ему над написать?\n`True` при успешной отправке. `False` при отсутствии пользователя в сети, или при неправильном токене."""
        url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/send_dm"
        formatted_buttons = []
        for button in buttons:
            formatted_buttons.append(button.data)
        params = {"username":username, "content":content, 'buttons':dumps(formatted_buttons)}
        headers = {"X-Bot-Token": self.token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, proxy=self.proxies, headers=headers) as r:
                    if r.status != 200:
                        if self.raise_on_status_code:
                            raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                        else:
                            return False
                    else:
                        return True
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента aiohttp: {e}")
            return False

    async def send_reply(self, message, content: str, buttons: list[Button] = []) -> bool:
        """Функция для ответа на чужое сообщение в мессенджере.\nmessage: экземпляр класса "Message", или ID сообщения (int).\ncontent: сообщение; как надо ответить на запрос.\nВозвращает True/False."""
        if isinstance(message, int):
            url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/send_reply"
            formatted_buttons = []
            for button in buttons:
                formatted_buttons.append(button.data)
            params = {"reply_to":message, "content":content, 'buttons':dumps(formatted_buttons)}
            headers = {"X-Bot-Token": self.token}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, params=params, proxy=self.proxies, headers=headers) as r:
                        if r.status != 200:
                            if self.raise_on_status_code:
                                raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                            else:
                                return False
                        else:
                            return True
            except aiohttp.ClientError as e:
                print(f"Ошибка клиента aiohttp: {e}")
                return False
        elif isinstance(message, Message):
            url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/send_reply"
            params = {"reply_to":message.id, "content":content}
            headers = {"X-Bot-Token": self.token}
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, params=params, proxy=self.proxies, headers=headers) as r:
                        if r.status != 200:
                            if self.raise_on_status_code:
                                raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                            else:
                                return False
                        else:
                            return True
            except aiohttp.ClientError as e:
                print(f"Ошибка клиента aiohttp: {e}")
                return False
        else:
            raise Exception(f'Неизвестный тип данных в аргументе message. Только класс Message и int!')

    async def get_blogs(self) -> list[Post]:
        """Асинхронный список постов с `/blogs`."""
        url = f"https://florestmsgs-florestdev4185.amvera.io/api/bot/get_blogs"
        headers = {"X-Bot-Token": self.token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, proxy=self.proxies) as r:
                    if r.status != 200:
                        if self.raise_on_status_code:
                            raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                        else:
                            return []
                    else:
                        data = await r.json()
                        posts = [Post(i) for i in data.get("blogs", [])]
                        return posts
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента aiohttp: {e}")
            return []

    async def get_message(self, id_msg: int):
        """Получить сообщение по ID.\nid_msg: ID сообщения.\nВозвращает Message/None, или ошибку, если включен raise_on_status_code."""
        url = "https://florestmsgs-florestdev4185.amvera.io/api/bot/get_message"
        headers = {"X-Bot-Token": self.token}
        params = {"id":id_msg}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, proxy=self.proxies, params=params) as r:
                    if r.status != 200:
                        if self.raise_on_status_code:
                            raise Exception(f"ОШИБКА! КОД: {r.status}. JSON: {await r.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                        else:
                            return
                    else:
                        data = await r.json().get('message')
                        return Message(data)
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента aiohttp: {e}")
            return 

    async def _process_message(self, message_data):
        """Асинхронная обработка одного сообщения."""
        if message_data in self.start_messages:
            return  # Пропустить, если сообщение уже обработано

        if message_data.get("username") != self.username:  # Используем username
            for handler in self.command_handlers:
                content = message_data.get("content")
                if content and content.startswith(handler.get('name')):
                    await handler["func"](Message(message_data))

        self.start_messages.append(message_data)

    async def _process_click(self, click: Dict[str, Any]):
        """Process a single button click."""
        if click in self.start_clicks:
            return
        if self.callback_handler_set:
            callback = CallBack(click)
            # Ensure callback_handler_set is awaitable if it's an async function
            if asyncio.iscoroutinefunction(self.callback_handler_set):
                await self.callback_handler_set(callback)
            else:
                self.callback_handler_set(callback)
        self.start_clicks.append(click)

    async def polling(self):
        """Asynchronous function to poll the API for new messages and clicks."""
        messages_url = "https://florestmsgs-florestdev4185.amvera.io/api/bot/get_messages"
        clicks_url = "https://florestmsgs-florestdev4185.amvera.io/api/bot/get_clicks"
        headers = {"X-Bot-Token": self.token}

        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    try:
                        # Poll for new messages
                        async with session.get(messages_url, headers=headers, proxy=self.proxies) as msg_response:
                            if msg_response.status != 200:
                                if self.raise_on_status_code:
                                    print(f'{Fore.RED}Fucking exception! Stopping the polling..')
                                    raise Exception(f"ОШИБКА! КОД: {msg_response.status}. JSON: {await msg_response.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                                else:
                                    print(f'{Fore.RED}Messages API Error: {msg_response.status}')
                                    await asyncio.sleep(1)
                                    continue
                            data = await msg_response.json()
                            messages = data.get("messages", [])

                        # Poll for new clicks
                        async with session.get(clicks_url, headers=headers, proxy=self.proxies) as click_response:
                            if click_response.status != 200:
                                if self.raise_on_status_code:
                                    print(f'{Fore.RED}Fucking exception in click polling! Stopping the polling..')
                                    raise Exception(f"ОШИБКА! КОД: {click_response.status}. JSON: {await click_response.json()}. ПРОВЕРЬТЕ ТОКЕН И ПРАВИЛЬНОСТЬ УКАЗАННЫХ ПАРАМЕТРОВ!!!")
                                else:
                                    print(f'{Fore.RED}Clicks API Error: {click_response.status}')
                                    await asyncio.sleep(1)
                                    continue
                            click_data = await click_response.json()
                            clicks = click_data.get("clicks", [])

                        # Process messages and clicks concurrently
                        message_tasks = [self._process_message(message) for message in messages]
                        click_tasks = [self._process_click(click) for click in clicks]
                        await asyncio.gather(*(message_tasks + click_tasks))

                    except aiohttp.ClientError as e:
                        print(f'{Fore.RED}aiohttp error during polling: {e}')
                        await asyncio.sleep(5)  # Longer delay for network errors
                    except Exception as e:
                        print(f'{Fore.RED}Unexpected error during polling: {e}')
                        await asyncio.sleep(5)

                    await asyncio.sleep(1)  # Delay before next poll

        except Exception as e:
            print(f'{Fore.RED}Global error in polling loop: {e}')
            if self.raise_on_status_code:
                raise



    def run(self):
        """Функция для старта бота."""
        print(f'{Fore.YELLOW}STARTING OF POLLING FROM FLORESTMESSANGER\'S API!')
        asyncio.run(self.polling())