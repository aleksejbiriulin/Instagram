import sys
import threading
import time
import base64
from queue import Queue
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QTextEdit, QScrollArea,
                             QMessageBox, QStackedWidget, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from setting import *
import Clientapi


class Communicate(QObject):
    update_signal = pyqtSignal(str)


class SocialNetworkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.posts = []
        self.current_user = None
        self.update_queue = Queue()
        self.stop_thread = False
        self.cl = Clientapi.CClientBL(SERVER_HOST, PORT)
        self.cl.connect()
        self.current_image_data = None

        self.comm = Communicate()
        self.comm.update_signal.connect(self.handle_update)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_main_page()
        self.init_profile_page()
        self.start_update_thread()

    def init_main_page(self):
        self.main_page = QWidget()
        self.main_layout = QVBoxLayout(self.main_page)

        self.header_layout = QHBoxLayout()

        self.profile_btn = QPushButton("Профиль")
        self.profile_btn.setVisible(False)
        self.profile_btn.clicked.connect(self.show_profile_page)

        self.add_post_btn = QPushButton("Добавить пост")
        self.add_post_btn.setVisible(False)
        self.add_post_btn.clicked.connect(self.show_add_post_dialog)

        self.login_btn = QPushButton("Войти")
        self.login_btn.clicked.connect(self.show_login_dialog)

        self.register_btn = QPushButton("Регистрация")
        self.register_btn.clicked.connect(self.show_register_dialog)

        self.header_layout.addWidget(self.profile_btn)
        self.header_layout.addWidget(self.add_post_btn)
        self.header_layout.addWidget(self.login_btn)
        self.header_layout.addWidget(self.register_btn)

        self.posts_label = QLabel("Список постов:")
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addWidget(self.posts_label)
        self.main_layout.addWidget(self.scroll_area)

        self.stacked_widget.addWidget(self.main_page)
        self.init_dialogs()
        self.update_posts()

    def init_profile_page(self):
        self.profile_page = QWidget()
        profile_layout = QVBoxLayout(self.profile_page)
        self.profile_login_label = QLabel(f"Ваши монеты: {self.calculate_user_activity()}")
        self.profile_login_label.setAlignment(Qt.AlignCenter)
        self.profile_login_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.profile_activity_label = QLabel("0")
        self.profile_activity_label.setAlignment(Qt.AlignCenter)
        self.profile_activity_label.setStyleSheet("font-size: 24px;")

        back_btn = QPushButton("Вернуться на главную")
        back_btn.clicked.connect(self.show_main_page)

        profile_layout.addStretch(1)
        profile_layout.addWidget(self.profile_login_label)
        profile_layout.addWidget(self.profile_activity_label)
        profile_layout.addStretch(1)
        profile_layout.addWidget(back_btn)
        profile_layout.addStretch(1)

        self.stacked_widget.addWidget(self.profile_page)

    def init_dialogs(self):
        self.register_dialog = QWidget()
        self.register_dialog.setWindowTitle("Регистрация")
        self.register_dialog.setFixedSize(300, 200)

        layout = QVBoxLayout()
        self.register_login_input = QLineEdit()
        self.register_password_input = QLineEdit()
        self.register_password_input.setEchoMode(QLineEdit.Password)
        register_btn = QPushButton("Зарегистрироваться")
        register_btn.clicked.connect(self.register)

        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.register_login_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.register_password_input)
        layout.addWidget(register_btn)

        self.register_dialog.setLayout(layout)

        self.login_dialog = QWidget()
        self.login_dialog.setWindowTitle("Вход")
        self.login_dialog.setFixedSize(300, 200)

        layout = QVBoxLayout()
        self.login_login_input = QLineEdit()
        self.login_password_input = QLineEdit()
        self.login_password_input.setEchoMode(QLineEdit.Password)
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.login)

        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_login_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.login_password_input)
        layout.addWidget(login_btn)

        self.login_dialog.setLayout(layout)

        self.add_post_dialog = QWidget()
        self.add_post_dialog.setWindowTitle("Новый пост")
        self.add_post_dialog.setFixedSize(400, 400)

        layout = QVBoxLayout()
        self.post_title_input = QLineEdit()
        self.post_content_input = QTextEdit()

        self.image_label = QLabel("Изображение не выбрано")
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(200, 150)
        self.image_preview.setStyleSheet("border: 1px solid black;")
        self.image_preview.setAlignment(Qt.AlignCenter)

        upload_btn = QPushButton("Выбрать изображение")
        upload_btn.clicked.connect(self.select_image)

        self.remove_image_btn = QPushButton("Удалить изображение")
        self.remove_image_btn.clicked.connect(self.remove_image)
        self.remove_image_btn.setEnabled(False)

        post_btn = QPushButton("Опубликовать")
        post_btn.clicked.connect(self.add_post)

        layout.addWidget(QLabel("Заголовок:"))
        layout.addWidget(self.post_title_input)
        layout.addWidget(QLabel("Содержание:"))
        layout.addWidget(self.post_content_input)
        layout.addWidget(QLabel("Изображение:"))
        layout.addWidget(upload_btn)
        layout.addWidget(self.remove_image_btn)
        layout.addWidget(self.image_label)
        layout.addWidget(self.image_preview)
        layout.addWidget(post_btn)

        self.add_post_dialog.setLayout(layout)

        self.comments_dialog = QWidget()
        self.comments_dialog.setWindowTitle("Комментарии")
        self.comments_dialog.setFixedSize(400, 300)

        self.comments_layout = QVBoxLayout()
        self.comments_scroll = QScrollArea()
        self.comments_widget = QWidget()
        self.comments_inner_layout = QVBoxLayout(self.comments_widget)

        self.comments_scroll.setWidgetResizable(True)
        self.comments_scroll.setWidget(self.comments_widget)

        self.comment_input = QLineEdit()
        self.add_comment_btn = QPushButton("Добавить комментарий")
        self.add_comment_btn.clicked.connect(self.add_comment)

        self.comments_layout.addWidget(self.comments_scroll)
        self.comments_layout.addWidget(self.comment_input)
        self.comments_layout.addWidget(self.add_comment_btn)

        self.comments_dialog.setLayout(self.comments_layout)

    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_name:
            try:
                with open(file_name, "rb") as image_file:
                    self.current_image_data = base64.b64encode(image_file.read()).decode('utf-8')

                pixmap = QPixmap(file_name)
                self.image_preview.setPixmap(pixmap.scaled(
                    self.image_preview.width(),
                    self.image_preview.height(),
                    Qt.KeepAspectRatio
                ))
                self.image_label.setText("Изображение выбрано")
                self.remove_image_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить изображение: {str(e)}")
                self.remove_image()

    def remove_image(self):
        self.current_image_data = None
        self.image_preview.clear()
        self.image_preview.setText("Превью изображения")
        self.image_label.setText("Изображение не выбрано")
        self.remove_image_btn.setEnabled(False)

    def calculate_user_activity(self):
        if self.current_user:
            self.cl.send_data(f"qc{self.current_user['login']}")
            return self.cl.receive_data()
        else:
            return ""

    def show_profile_page(self):
        if not self.current_user:
            QMessageBox.warning(self, "Ошибка", "Пользователь не авторизован")
            return

        self.profile_login_label.setText(self.current_user['login'])
        activity = self.calculate_user_activity()
        self.profile_activity_label.setText(str(activity))

        self.stacked_widget.setCurrentIndex(1)

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_login_dialog(self):
        self.login_dialog.show()

    def show_register_dialog(self):
        self.register_dialog.show()

    def show_add_post_dialog(self):
        self.add_post_dialog.show()

    def show_comments(self, post_id):
        self.current_post_id = post_id
        for post in self.posts:
            if post["id"] == post_id:
                while self.comments_inner_layout.count():
                    item = self.comments_inner_layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()

                for comment in post["comments"]:
                    label = QLabel(f"{comment['user']}: {comment['text']}")
                    self.comments_inner_layout.addWidget(label)

                self.comments_dialog.setWindowTitle(f"Комментарии к посту {post_id}")
                self.comments_dialog.show()
                break

    def update_header(self):
        if self.current_user:
            self.profile_btn.setText(f"Профиль ({self.current_user['login']})")
            self.profile_btn.setVisible(True)
            self.add_post_btn.setVisible(True)
            self.login_btn.setVisible(False)
            self.register_btn.setVisible(False)
        else:
            self.profile_btn.setVisible(False)
            self.add_post_btn.setVisible(False)
            self.login_btn.setVisible(True)
            self.register_btn.setVisible(True)

    def register(self):
        login = self.register_login_input.text()
        password = self.register_password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Логин и пароль не могут быть пустыми")
            return

        self.cl.send_data(f"au{login}|{password}")
        result = self.cl.receive_data()

        if result != "ok":
            QMessageBox.warning(self, "Ошибка", "Логин уже используется")
            return

        self.current_user = {"login": login, "password": password}
        QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован!")
        self.register_dialog.hide()
        self.update_posts()
        self.update_header()

    def login(self):
        login = self.login_login_input.text()
        password = self.login_password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Логин и пароль не могут быть пустыми")
            return

        self.cl.send_data(f"lu{login}|{password}")
        result = self.cl.receive_data()
        print(result)
        if result != "ok":
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            return

        self.current_user = {"login": login, "password": password}
        QMessageBox.information(self, "Успех", "Пользователь успешно вошёл!")
        self.login_dialog.hide()
        self.update_posts()
        self.update_header()

    def logout(self):
        self.current_user = None
        self.profile_dialog.hide()
        QMessageBox.information(self, "Успех", "Вы успешно вышли из аккаунта")
        self.update_header()

    def add_post(self):
        title = self.post_title_input.text()
        content = self.post_content_input.toPlainText()

        if not title or not content:
            QMessageBox.warning(self, "Ошибка", "Заголовок и содержание не могут быть пустыми")
            return
        # print(f"ap{self.current_user['login']}|{title}|{content}|{self.current_image_data}")
        self.cl.send_data(f"ap{self.current_user['login']}|{title}|{content}|{self.current_image_data}")
        post_id = int(self.cl.receive_data())
        self.cl.send_data(f"sc{self.current_user['login']}|50")
        result = self.cl.receive_data()

        self.posts.append({
            "id": post_id,
            "auth": self.current_user['login'],
            "title": title,
            "content": content,
            "comments": [],
            "image": self.current_image_data
        })

        QMessageBox.information(self, "Успех", "Пост успешно добавлен!")
        self.add_post_dialog.hide()
        self.post_title_input.clear()
        self.post_content_input.clear()
        self.remove_image()
        self.update_posts()

    def add_comment(self):
        comment_text = self.comment_input.text()
        if not self.current_user:
            QMessageBox.warning(self, "Ошибка", "Войдите в аккаунт чтобы добавить пост")
            return
        if not comment_text or not self.current_user:
            QMessageBox.warning(self, "Ошибка", "Текст комментария не может быть пустым")
            return
        self.cl.send_data(f"sc{self.current_user['login']}|-10")
        result = self.cl.receive_data()
        if result != "ok":
            QMessageBox.warning(self, "Ошибка", "Недостаточно средств")
            return
        self.cl.send_data(f"ac{self.current_post_id}|{self.current_user['login']}|{comment_text}")
        result = self.cl.receive_data()
        if result != "ok":
            QMessageBox.warning(self, "Ошибка", "Ошибка соединения с сервером")
            return

        for post in self.posts:
            if post["id"] == self.current_post_id:
                post["comments"].append({
                    "user": self.current_user["login"],
                    "text": comment_text
                })
                break

        self.comment_input.clear()
        self.show_comments(self.current_post_id)

    def update_posts(self):
        self.posts.clear()
        i = 1

        while True:
            self.cl.send_data(f"rp{i}")
            msg = self.cl.receive_data()
            print(msg)
            if msg == "no":
                break

            msg = msg.split("|")
            if len(msg) != 4:
                break

            auth, title, text, image = msg
            self.posts.append({
                "id": i,
                "auth": auth,
                "title": title,
                "content": text,
                "comments": [],
                "image": image
            })

            self.cl.send_data(f"rc{i}")
            result = self.cl.receive_data()

            for j in result.split(";"):
                if j != "":
                    if len(j.split("|")) != 2:
                        continue
                    user, comment_text = j.split("|")
                    self.posts[-1]["comments"].append({
                        "user": user,
                        "text": comment_text
                    })

            i += 1

        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        print(self.posts)
        for post in self.posts:
            post_widget = QWidget()
            post_layout = QVBoxLayout(post_widget)

            title_label = QLabel(f"Пост {post['id']}: {post['title']}")
            content_label = QLabel(post["content"])
            comments_btn = QPushButton(f"Комментарии")
            comments_btn.clicked.connect(lambda _, pid=post['id']: self.show_comments(pid))

            post_layout.addWidget(title_label)
            post_layout.addWidget(content_label)
            if post.get("image"):
                image_label = QLabel()
                pixmap = QPixmap()
                pixmap.loadFromData(base64.b64decode(post["image"]))
                image_label.setPixmap(pixmap.scaled(200, 150, Qt.KeepAspectRatio))
                post_layout.addWidget(image_label)

            post_layout.addWidget(comments_btn)

            self.scroll_layout.addWidget(post_widget)

    def start_update_thread(self):
        self.update_thread = threading.Thread(target=self.check_updates, daemon=True)
        self.update_thread.start()

    def check_updates(self):
        while not self.stop_thread:
            try:
                self.cl.send_data("cp")
                result = int(self.cl.receive_data())

                if result != len(self.posts):
                    self.comm.update_signal.emit("update_posts")
                else:
                    self.cl.send_data(f"cc")
                    result = self.cl.receive_data()
                    if int(result) != sum(len(post["comments"]) for post in self.posts):
                        self.comm.update_signal.emit("update_posts")
            except Exception as e:
                print(f"Ошибка при проверке обновлений: {e}")

            time.sleep(5)

    def handle_update(self, msg):
        if msg == "update_posts":
            self.update_posts()
            # QMessageBox.information(self, "Обновление", "Появились новые посты или комментарии!")

    def closeEvent(self, event):
        self.stop_thread = True
        self.cl.disconnect()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SocialNetworkApp()
    window.show()
    sys.exit(app.exec_())