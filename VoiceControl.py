import speech_recognition as sr

def listen_and_recognize():
    """
    Слушает микрофон и возвращает распознанный текст.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Слушаю... (скажите что-нибудь)")
        
        # Настройка на уровень шума в помещении
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        try:
            # Захват аудио (ждём фразу, таймаут 5 секунд)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("✅ Захвачено, распознаю...")
            
            # Распознавание с помощью Google Speech Recognition (нужен интернет)
            text = recognizer.recognize_google(audio, language="ru-RU")
            print(f"📝 Распознано: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("⏰ Время ожидания истекло. Вы ничего не сказали.")
            return None
        except sr.UnknownValueError:
            print("❓ Не удалось распознать речь.")
            return None
        except sr.RequestError as e:
            print(f"🌐 Ошибка соединения с сервисом распознавания: {e}")
            return None

# Запуск функции
if __name__ == "__main__":
    result = listen_and_recognize()
    if result:
        print(f"Результат: {result}")