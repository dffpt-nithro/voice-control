import speech_recognition as sr
import os

def listen_and_recognize():
    """
    Слушает микрофон и возвращает распознанный текст.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Слушаю... (скажите команду)")
        
        # Пробуем настроить шумоподавление
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception:
            pass  # Продолжаем без настройки
        
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


def execute_command(text):
    """
    Выполняет действие в зависимости от распознанной команды.
    """
    if text is None:
        return True
    
    # === КОМАНДЫ ДЛЯ ОТКРЫТИЯ БЛОКНОТА ===
    notepad_keywords = [
        "открой блокнот",
        "открыть блокнот",
        "запусти блокнот",
        "запустить блокнот",
        "открой notepad",
        "open notepad"
    ]
    
    if matches_command(text, notepad_keywords):
        print("🚀 Запускаю Блокнот...")
        os.system("start notepad.exe")
        return True
    
    # === КОМАНДЫ ДЛЯ ЗАКРЫТИЯ БЛОКНОТА ===
    close_notepad_keywords = [
        "закрой блокнот",
        "закрыть блокнот",
        "убери блокнот",
        "сверни блокнот",
        "закрой notepad",
        "close notepad"
    ]
    
    if matches_command(text, close_notepad_keywords):
        print("🔒 Закрываю Блокнот...")
        os.system("taskkill /f /im notepad.exe 2>nul")
        print("   Блокнот закрыт (если был открыт).")
        return True
    
    # === КОМАНДЫ ВЫХОДА ===
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
    
    if matches_command(text, exit_keywords):
        print("👋 Завершение работы программы...")
        return False


# ====== ЗАПУСК ПРОГРАММЫ ======
if __name__ == "__main__":
    print("=" * 50)
    print("🎙️  ГОЛОСОВОЙ ПОМОЩНИК ЗАПУЩЕН")
    print('📋 Команды: "Открой блокнот", "Закрой блокнот"')
    print('   Для выхода: "Выход", "Закрой программу"')
    print("=" * 50)
    
    running = True
    while running:
        text = listen_and_recognize()
        if text:
            running = execute_command(text)
        print("-" * 40)