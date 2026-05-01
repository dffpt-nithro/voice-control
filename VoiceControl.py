import speech_recognition as sr
import os
from PyQt5.QtCore import QThread, pyqtSignal

class RecognitionThread(QThread):
    """Поток для распознавания речи - интегрирован с UI"""
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.recognizer = sr.Recognizer()
        
    def run(self):
        self.is_running = True
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception:
                pass
            self.recognizer.energy_threshold = 300
            
            while self.is_running:
                try:
                    print("🎤 Слушаю... (скажите команду)")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=20)
                    print("✅ Захвачено, распознаю...")
                    text = self.recognizer.recognize_google(audio, language="ru-RU")
                    print(f"📝 Распознано: {text}")
                    self.text_recognized.emit(text.lower())
                    
                except sr.WaitTimeoutError:
                    print("⏰ Время ожидания истекло. Вы ничего не сказали.")
                    pass
                except sr.UnknownValueError:
                    print("❓ Не удалось распознать речь. Попробуйте ещё раз.")
                    self.error_occurred.emit("❌ Не удалось распознать речь")
                except sr.RequestError as e:
                    print(f"🌐 Ошибка соединения с сервисом распознавания: {e}")
                    self.error_occurred.emit(f"🌐 Ошибка соединения: {e}")
                except Exception as e:
                    print(f"Ошибка: {e}")
                    
    def stop(self):
        self.is_running = False

class VoiceCommandProcessor:
    """
    Класс для обработки голосовых команд - интегрирован с UI
    """
    
    @staticmethod
    def listen_and_recognize():
        """
        Слушает микрофон и возвращает распознанный текст.
        """
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            print("🎤 Слушаю... (скажите команду)")
            
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception:
                pass  
            
            recognizer.energy_threshold = 300
            
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("✅ Захвачено, распознаю...")
                text = recognizer.recognize_google(audio, language="ru-RU")
                print(f"📝 Распознано: {text}")
                return text.lower()
                
            except sr.WaitTimeoutError:
                print("⏰ Время ожидания истекло. Вы ничего не сказали.")
                return None
            except sr.UnknownValueError:
                print("❓ Не удалось распознать речь. Попробуйте ещё раз.")
                return None
            except sr.RequestError as e:
                print(f"🌐 Ошибка соединения с сервисом распознавания: {e}")
                return None

    @staticmethod
    def matches_command(text, keywords):
        """
        Проверяет, содержится ли в тексте хотя бы одна из ключевых фраз.
        """
        if text is None:
            return False
        
        for keyword in keywords:
            if keyword in text:
                return True
        return False

    @staticmethod
    def execute_command(text, callback_success=None, callback_error=None, callback_update=None):
        """
        Выполняет действие в зависимости от распознанной команды.
        
        Args:
            text: распознанный текст
            callback_success: функция обратного вызова при успехе
            callback_error: функция обратного вызова при ошибке
            callback_update: функция обновления статуса
        """
        if text is None:
            return True
        
        notepad_keywords = [
            "открой блокнот",
            "открыть блокнот",
            "запусти блокнот",
            "запустить блокнот",
            "открой notepad",
            "open notepad"
        ]
        
        if VoiceCommandProcessor.matches_command(text, notepad_keywords):
            print("🚀 Запускаю Блокнот...")
            try:
                os.system("notepad.exe")
                if callback_success:
                    callback_success("✅ Блокнот успешно открыт")
                if callback_update:
                    callback_update("открыт блокнот")
                return True
            except Exception as e:
                if callback_error:
                    callback_error(f"Ошибка при открытии блокнота: {e}")
                return True
        
        close_notepad_keywords = [
            "закрой блокнот",
            "закрыть блокнот",
            "убери блокнот",
            "сверни блокнот",
            "закрой notepad",
            "close notepad"
        ]
        
        if VoiceCommandProcessor.matches_command(text, close_notepad_keywords):
            print("🔒 Закрываю Блокнот...")
            os.system("taskkill /f /im notepad.exe 2>nul")
            print("   Блокнот закрыт (если был открыт).")
            if callback_success:
                callback_success("✅ Блокнот закрыт")
            if callback_update:
                callback_update("закрыт блокнот")
            return True
        
        exit_keywords = [
            "выход",
            "выйти",
            "закрой программу",
            "закрыть программу",
            "стоп",
            "exit",
            "quit",
            "останови программу"
        ]
        
        if VoiceCommandProcessor.matches_command(text, exit_keywords):
            print("👋 Завершение работы программы...")
            if callback_success:
                callback_success("👋 Завершение работы...")
            return False
        
        print(f"ℹ️ Команда не распознана. Попробуйте:")
        print('   - "Открой блокнот" / "Запусти блокнот"')
        print('   - "Закрой блокнот"')
        print('   - "Выход" / "Закрой программу"')
        
        if callback_error:
            callback_error(f"❌ Команда не распознана: '{text}'\n\nДоступные команды:\n• Открой блокнот\n• Закрой блокнот\n• Выход")
        if callback_update:
            callback_update("команда не распознана")
        return True


if __name__ == "__main__":
    print("=" * 50)
    print("🎙️  ГОЛОСОВОЙ ПОМОЩНИК ЗАПУЩЕН (консольный режим)")
    print('📋 Команды: "Открой блокнот", "Закрой блокнот"')
    print('   Для выхода: "Выход", "Закрой программу"')
    print("=" * 50)
    
    running = True
    while running:
        text = VoiceCommandProcessor.listen_and_recognize()
        if text:
            running = VoiceCommandProcessor.execute_command(text)
        print("-" * 40)