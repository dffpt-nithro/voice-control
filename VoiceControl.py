import speech_recognition as sr
import os
from PyQt5.QtCore import QThread, pyqtSignal


class RecognitionThread(QThread):
    """Поток для однократного распознавания речи"""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()

    def run(self):
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception:
                pass
            self.recognizer.energy_threshold = 300

            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio, language="ru-RU")
                self.text_recognized.emit(text.lower())
            except sr.WaitTimeoutError:
                self.error_occurred.emit("⏰ Время вышло")
            except sr.UnknownValueError:
                self.error_occurred.emit("❓ Не распознано")
            except sr.RequestError as e:
                self.error_occurred.emit(f"🌐 Ошибка соединения: {e}")
            except Exception as e:
                self.error_occurred.emit(f"Ошибка: {e}")


class VoiceCommandProcessor:
    """Обработчик команд"""

    @staticmethod
    def matches_command(text, keywords):
        if text is None:
            return False
        for keyword in keywords:
            if keyword in text:
                return True
        return False

    @staticmethod
    def execute_command(text, callback_update=None):
        if text is None:
            return True

        notepad_keywords = [
            "открой блокнот", "открыть блокнот", "запусти блокнот",
            "запустить блокнот", "открой notepad", "open notepad"
        ]
        if VoiceCommandProcessor.matches_command(text, notepad_keywords):
            os.system("start notepad.exe")
            if callback_update:
                callback_update("✅ блокнот открыт")
            return True

        close_notepad_keywords = [
            "закрой блокнот", "закрыть блокнот", "убери блокнот",
            "сверни блокнот", "закрой notepad", "close notepad"
        ]
        if VoiceCommandProcessor.matches_command(text, close_notepad_keywords):
            os.system("taskkill /f /im notepad.exe 2>nul")
            if callback_update:
                callback_update("✅ блокнот закрыт")
            return True

        exit_keywords = [
            "выход", "выйти", "закрой программу", "закрыть программу",
            "стоп", "exit", "quit", "останови программу"
        ]
        if VoiceCommandProcessor.matches_command(text, exit_keywords):
            if callback_update:
                callback_update("👋 выход из программы")
            return False

        if callback_update:
            callback_update("команда не распознана")
        return True


if __name__ == "__main__":
    print("=" * 50)
    print("🎙️  ГОЛОСОВОЙ ПОМОЩНИК (консольный режим)")
    print('📋 Команды: "Открой блокнот", "Закрой блокнот", "Выход"')
    print("=" * 50)

    recognizer = sr.Recognizer()
    running = True
    while running:
        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception:
                pass
            recognizer.energy_threshold = 300

            try:
                print("\n🎤 Слушаю...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio, language="ru-RU")
                print(f"📝 Распознано: {text}")
                running = VoiceCommandProcessor.execute_command(text.lower())
            except sr.WaitTimeoutError:
                print("⏰ Ничего не сказано")
            except sr.UnknownValueError:
                print("❓ Не распознано")
            except sr.RequestError as e:
                print(f"🌐 Ошибка: {e}")