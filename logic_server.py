import sqlite3

class User:

    def __init__(self, login, password):
        self.login = login
        self.password = password

class Comment:

    def __init__(self, auth, text):
        self.auth = auth
        self.text = text

def get_user_by_id(user_id):
    if not isinstance(user_id, int):
        print(f"Ошибка: ID должен быть числом, получено {type(user_id)}")
        return None
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, login, coins FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            return None
        return {
            "id": user_data[0],
            "login": user_data[1],
            "coins": user_data[2],
        }

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_user_by_login(login):
    conn = None
    try:
        print(login)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, login, coins FROM users WHERE login = ?', (login,))
        user_data = cursor.fetchone()
        if not user_data:
            return None
        print(user_data)
        return {
            "id": user_data[0],
            "login": user_data[1],
            "coins": user_data[2],
        }

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return None
    finally:
        if conn:
            conn.close()

def check_login_password(login: str, password: str) -> str:
    # Подключение к базе данных
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # Поиск пользователя по логину
        cursor.execute('SELECT password FROM users WHERE login = ?', (login,))
        result = cursor.fetchone()  # Получаем первую строку результата
        if result:
            # Если пользователь найден, проверяем пароль
            db_password = result[0]  # Пароль из базы данных
            if password == db_password:
                return "ok"  # Логин и пароль верны
            else:
                return "no"  # Пароль неверный
        else:
            return "no"  # Пользователь не найден
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return "no"  # В случае ошибки возвращаем "no"
    finally:
        # Закрываем соединение с базой данных
        conn.close()

def add_user(login, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # Пытаемся вставить нового пользователя
        cursor.execute('INSERT INTO users (login, password) VALUES (?, ?)', (login, password))
        conn.commit()
        return "ok"
    except sqlite3.IntegrityError:
        # Если возникает ошибка уникальности (пользователь уже существует)
        return "no"
    finally:
        conn.close()

def add_post(auth, title, post_text, image):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM users WHERE login = ?', (auth,))
        result = cursor.fetchone()
        if result is None:
            return -1
        auth_id = result[0]
        cursor.execute('INSERT INTO posts (auth_id, text, image) VALUES (?, ?, ?)', (auth_id, title + "|" + post_text, image))
        post_id = cursor.lastrowid
        conn.commit()
        return post_id
    except Exception as e:
        return -1
    finally:
        conn.close()

def read_post(post_id):
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Получаем данные поста
        cursor.execute('''
            SELECT p.text, p.auth_id, p.image
            FROM posts p
            WHERE p.id = ?
        ''', (post_id,))

        post_data = cursor.fetchone()
        print(post_data)
        if not post_data:
            return "no"
        post_text = post_data[0]
        return f"{get_user_by_id(post_data[1])["login"]}|{post_text}|{post_data[2]}"
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return ""
    finally:
        if conn:
            conn.close()

def get_posts_count():
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) 
            FROM posts 
        ''')

        count = cursor.fetchone()[0]
        return str(count)
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return ""
    finally:
        if conn:
            conn.close()

def add_comment(post_id, user_login, comment_text):
    conn = None
    user_id = get_user_by_login(user_login)
    user_id = user_id["id"]
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Вставляем комментарий в таблицу
        cursor.execute('''
            INSERT INTO comments (post_id, auth_id, text)
            VALUES (?, ?, ?)
        ''', (post_id, user_id, comment_text))

        conn.commit()
        return "ok"

    except sqlite3.Error as e:
        print(f"Ошибка при добавлении комментария: {e}")
        return "no"

    finally:
        if conn:
            conn.close()

def get_comments_count():
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) 
            FROM comments 
        ''')

        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        print(f"Ошибка при получении количества комментариев: {e}")
        return None

    finally:
        if conn:
            conn.close()

def get_comments_as_string(post_id):
    conn = None
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.login, c.text 
            FROM comments c
            JOIN users u ON c.auth_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.id
        ''', (post_id,))
        comments = cursor.fetchall()
        if not comments:
            return ""
        comments_str = ";".join([f"{user}|{text}" for user, text in comments])
        return comments_str

    except sqlite3.Error as e:
        print(f"Ошибка при получении комментариев: {e}")
        return None

    finally:
        if conn:
            conn.close()

def update_user_coins(login, coin_change):
    user = get_user_by_login(login)
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            # Проверяем, чтобы баланс не ушел в минус (если требуется)
            new_balance = user['coins'] + int(coin_change)
            if new_balance < 0:  # Если хотим запрещать отрицательный баланс
                return "no"

            # Обновляем баланс
            cursor.execute('''
                UPDATE users 
                SET coins = ? 
                WHERE id = ?
                RETURNING coins
            ''', (new_balance, user['id']))

            conn.commit()

            return "ok"
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return "no"

def response(msg: str) -> str:
    # логика ответа на запросы к серверу
    """
    au - добавление пользователя
    lu - проверка правильности логина и пароля
    ac - добавление комментария
    rc - прочтения всех комментариев i-ого поста
    ap - добавление поста
    rp - прочтения i-ого поста
    cp- подсчёт количества постов
    сс -  подсчёт количества комментариев по id поста
    qc - количество денег
    sc - добваление денег
    ir - тип работы с изображениям
    ig - возврат изображение
    """
    type_msg = msg[:2]
    msg = msg[2:]
    print(msg)
    if type_msg == "au":
        login, password = msg.split("|")
        return add_user(login, password)
    elif type_msg == "lu":
        login, password = msg.split("|")
        return check_login_password(login, password)
    elif type_msg == "ap":
        auth, title, text, image= msg.split("|")
        post_id = add_post(auth, title, text, image)
        if post_id == "-1":
            return "no"
        else:
            return str(post_id)
    elif type_msg == "rp":
        return read_post(int(msg))
    elif type_msg == "ac":
        post_id, auth, text = msg.split("|")
        post_id = int(post_id)
        return add_comment(post_id, auth, text)
    elif type_msg == "rc":
        return get_comments_as_string(int(msg))
    elif type_msg == "cp":
        return get_posts_count()
    elif type_msg == "cc":
        return get_comments_count()
    elif type_msg == "qc":
        return get_user_by_login(msg)["coins"]
    elif type_msg == "sc":
        return update_user_coins(*msg.split("|"))
