import speech_recognition as sr
import os

def listen_and_recognize():
    """
    Слушает микрофон и возвращает распознанный текст.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Слушаю... (скажите команду)")
        
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"⚠️ Не удалось настроить шумоподавление: {e}")
            print("Продолжаю без настройки...")
        
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

def execute_command(text):
    """
    Выполняет действие в зависимости от распознанной команды.
    """
    if text is None:
        return
    
    if "блокнот" in text:
        print("🚀 Запускаю Блокнот...")
        os.system("notepad.exe")
    
    elif "notepad" in text:
        print("🚀 Opening Notepad...")
        os.system("notepad.exe")
    
    elif "выход" in text or "exit" in text or "quit" in text:
        print("👋 Завершение работы программы...")
        return False  
    
    else:
        print(f"ℹ️ Команда '{text}' не распознана. Доступные команды: 'блокнот', 'notepad', 'выход', 'exit'.")
    
    return True  

if __name__ == "__main__":
    print("=" * 50)
    print("🎙️  ГОЛОСОВОЙ ПОМОЩНИК ЗАПУЩЕН")
    print("📋 Доступные команды: 'блокнот' / 'notepad', 'выход' / 'exit'")
    print("=" * 50)
    
    running = True
    while running:
        text = listen_and_recognize()
        if text:
            running = execute_command(text)
        print("-" * 40)  