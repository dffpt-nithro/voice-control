import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from VoiceControl import RecognitionThread, VoiceCommandProcessor


class VoiceAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('form.ui', self)

        self.setMinimumSize(420, 680)
        self.resize(420, 680)

        self.recognition_thread = None
        self.is_listening = False

        self.recordButton_3.setText("🎤")
        self.recordButton_3.setStyleSheet(
            self.recordButton_3.styleSheet() + "QPushButton { font-size: 32px; }"
        )

        self.init_connections()
        self.show()
        self.update_status("готов")

    def init_connections(self):
        self.recordButton_3.clicked.connect(self.toggle_voice_recognition)
        self.sendCommandButton.clicked.connect(self.send_text_command)
        self.commandInput_3.returnPressed.connect(self.send_text_command)

    def toggle_voice_recognition(self):
        if self.is_listening:
            self.stop_voice_recognition()
        else:
            self.start_voice_recognition()

    def start_voice_recognition(self):
        self.is_listening = True
        self.update_status("🎙️ слушаю...")
        self.recordButton_3.setText("🔴")
        self.recordButton_3.setStyleSheet("""
            QPushButton {
                background-color: #330000; color: #ff4444;
                border: 2px solid #ff4444; border-radius: 60px;
                font-size: 32px; font-weight: bold; font-family: 'Arial';
            }
        """)

        self.recognition_thread = RecognitionThread()
        self.recognition_thread.text_recognized.connect(self.process_voice_command)
        self.recognition_thread.error_occurred.connect(self.on_recognition_error)
        self.recognition_thread.finished.connect(self.play_sound)  # 🔊 звук после распознавания
        self.recognition_thread.start()

    def stop_voice_recognition(self):
        self.is_listening = False
        if self.recognition_thread:
            self.recognition_thread.quit()
            self.recognition_thread.wait()
            self.recognition_thread = None

        self.update_status("готов")
        self.recordButton_3.setText("🎤")
        self.recordButton_3.setStyleSheet("""
            QPushButton {
                background-color: #0a0a0a; color: #88ccff;
                border: 2px solid #66ccff; border-radius: 60px;
                font-size: 32px; font-weight: bold; font-family: 'Arial';
            }
            QPushButton:hover {
                background-color: #1a1a1a; border: 2px solid #88ddff;
                box-shadow: 0 0 20px rgba(102, 204, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: #002233; border: 2px solid #aaffff;
            }
        """)

    def process_voice_command(self, text):
        """Получает текст из потока, выполняет команду"""
        self.update_status(f"распознано: {text}")
        running = VoiceCommandProcessor.execute_command(
            text,
            callback_update=self.update_status
            )
        self.stop_voice_recognition()  
        if not running:
            self.close()

    def on_recognition_error(self, message):
        """Ошибка распознавания"""
        self.update_status(message)
        self.stop_voice_recognition()
        self.play_sound()  

    def send_text_command(self):
        command = self.commandInput_3.text().strip()
        if not command:
            self.update_status("введите команду")
            return

        self.update_status(f"команда: {command}")
        running = VoiceCommandProcessor.execute_command(
            command.lower(),
            callback_update=self.update_status
        )
        self.commandInput_3.clear()
        self.play_sound()  
        if not running:
            self.close()

    def update_status(self, text):
        self.recognitionLabel_3.setText(f"распознано: {text}")

    def play_sound(self):
        """Проигрывает системный звук уведомления"""
        QApplication.beep()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = VoiceAssistant()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()