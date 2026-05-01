import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt
from VoiceControl import RecognitionThread, VoiceCommandProcessor


class VoiceAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Загружаем UI из файла form.ui
        uic.loadUi('form.ui', self)
        
        # Устанавливаем минимальный размер окна вместо фиксированного
        self.setMinimumSize(400, 650)
        self.resize(400, 650)
        
        # Инициализация переменных
        self.recognition_thread = None
        self.is_listening = False
        
        # Настройка иконки для кнопки записи
        self.recordButton_3.setText("🎤")
        self.recordButton_3.setStyleSheet(self.recordButton_3.styleSheet() + """
            QPushButton {
                font-size: 32px;
            }
        """)
        
        # Привязка сигналов к слотам
        self.init_connections()
        
        # Показываем окно
        self.show()
        
        # Статус готовности
        self.update_recognition_status("готов к работе")
        
    def init_connections(self):
        """Привязка всех кнопок и элементов UI к функциям обработки"""
        # Кнопка записи голоса — переключение по клику (Push-to-Toggle)
        self.recordButton_3.clicked.connect(self.toggle_voice_recognition)
        
        # Кнопка отправки текстовой команды (галочка)
        self.sendCommandButton.clicked.connect(self.send_text_command)
        
        # Поле ввода команды (по нажатию Enter)
        self.commandInput_3.returnPressed.connect(self.send_text_command)
        
    def toggle_voice_recognition(self):
        """Переключение режима записи по клику"""
        if self.is_listening:
            self.stop_voice_recognition()
        else:
            self.start_voice_recognition()
        
    def start_voice_recognition(self):
        """Начало распознавания голоса"""
        self.is_listening = True
        self.update_recognition_status("🎙️ слушаю...")
        self.recordButton_3.setText("🔴")
        
        # Изменяем стиль кнопки при записи
        self.recordButton_3.setStyleSheet("""
            QPushButton {
                background-color: #330000;
                color: #ff4444;
                border: 2px solid #ff4444;
                border-radius: 60px;
                font-size: 32px;
                font-weight: bold;
                font-family: 'Arial';
            }
        """)
        
        # Запускаем поток распознавания
        self.recognition_thread = RecognitionThread()
        self.recognition_thread.text_recognized.connect(self.process_voice_command)
        self.recognition_thread.error_occurred.connect(self.show_error_message)
        self.recognition_thread.start()
        
    def stop_voice_recognition(self):
        """Остановка распознавания голоса"""
        self.is_listening = False
        if self.recognition_thread:
            self.recognition_thread.stop()
            self.recognition_thread.wait()
            self.recognition_thread = None
            
        self.update_recognition_status("готов")
        self.recordButton_3.setText("🎤")
        
        # Восстанавливаем оригинальный стиль кнопки
        self.recordButton_3.setStyleSheet("""
            QPushButton {
                background-color: #0a0a0a;
                color: #88ccff;
                border: 2px solid #66ccff;
                border-radius: 60px;
                font-size: 32px;
                font-weight: bold;
                font-family: 'Arial';
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                border: 2px solid #88ddff;
                box-shadow: 0 0 20px rgba(102, 204, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: #002233;
                border: 2px solid #aaffff;
            }
        """)
        
    def process_voice_command(self, text):
        """Обработка голосовой команды из потока"""
        self.update_recognition_status(f"распознано: {text}")
        # Выполняем команду с callback-функциями для UI
        VoiceCommandProcessor.execute_command(
            text,
            callback_success=self.show_success_message,
            callback_error=self.show_error_message,
            callback_update=self.update_recognition_status
        )
        
    def send_text_command(self):
        """Отправка команды из текстового поля ввода"""
        command = self.commandInput_3.text().strip()
        if not command:
            self.show_error_message("Введите команду")
            return
            
        self.update_recognition_status(f"команда: {command}")
        # Выполняем команду с callback-функциями для UI
        running = VoiceCommandProcessor.execute_command(
            command.lower(),
            callback_success=self.show_success_message,
            callback_error=self.show_error_message,
            callback_update=self.update_recognition_status
        )
        
        # Очищаем поле ввода после отправки
        self.commandInput_3.clear()
        
        # Если команда завершения программы - закрываем приложение
        if not running:
            self.close()
        
    def update_recognition_status(self, status_text):
        """Обновление текста на метке распознавания"""
        full_text = f"распознано: {status_text}"
        self.recognitionLabel_3.setText(full_text)
        
    def show_error_message(self, message):
        """Показ сообщения об ошибке в диалоговом окне"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Ошибка")
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0a0a0a;
                color: #88ccff;
            }
            QMessageBox QLabel {
                color: #88ccff;
                min-width: 300px;
            }
            QPushButton {
                background-color: #0a0a0a;
                color: #88ccff;
                border: 1px solid #66ccff;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        msg.exec_()
        
    def show_success_message(self, message):
        """Показ сообщения об успехе в диалоговом окне"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Успех")
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0a0a0a;
                color: #88ccff;
            }
            QMessageBox QLabel {
                color: #88ccff;
                min-width: 300px;
            }
            QPushButton {
                background-color: #0a0a0a;
                color: #88ccff;
                border: 1px solid #66ccff;
                border-radius: 5px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """)
        msg.exec_()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = VoiceAssistant()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()