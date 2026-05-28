import speech_recognition as sr
import os
import time
import re
from PyQt5.QtCore import QThread, pyqtSignal


# ====== СЛОВАРИ КОМАНД ======

# Намерения (intents) — что сделать
INTENTS = {
    "volume_unmute": [
        "включи звук", "включить звук", "верни звук", "со звуком"
    ],
    "volume_mute": [
        "выключи звук", "отключи звук", "mute", "без звука"
    ],
    "volume_up": [
        "громче", "погромче", "прибавь громкость", "увеличь громкость",
        "повысь громкость", "volume up"
    ],
    "volume_down": [
        "тише", "потише", "убавь громкость", "уменьши громкость",
        "понизь громкость", "volume down"
    ],
    "volume_set": [
        "звук на", "громкость на", "поставь звук", "поставь громкость",
        "сделай звук", "сделай громкость", "уровень звука", "уровень громкости",
        "volume", "громкость"
    ],
    "open": [
        "открой", "открыть", "запусти", "запустить", "включи", "включить",
        "вруби", "start", "open", "launch"
    ],
    "close": [
        "закрой", "закрыть", "выключи", "выключить", "убери", "сверни",
        "stop", "close"
    ],
    "exit": [
        "выход", "выйди", "закрой программу", "закрыть программу",
        "стоп", "хватит", "exit", "quit"
    ],
}

# Объекты (entities) — над чем выполнить действие
ENTITIES = {
    "notepad": {
        "keywords": ["блокнот", "notepad"],
        "open_cmd": "start notepad.exe",
        "close_cmd": "taskkill /f /im notepad.exe 2>nul",
        "name": "Блокнот"
    },
    "calculator": {
        "keywords": ["калькулятор", "calculator", "calc"],
        "open_cmd": "start calc.exe",
        "close_cmd": 'powershell -command "Get-Process | Where-Object {$_.ProcessName -like \'*calc*\'} | Stop-Process -Force"',
        "name": "Калькулятор"
    },
    "browser": {
        "keywords": ["браузер", "browser", "интернет"],
        "open_cmd": "cmd /c start https://ya.ru",
        "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul || taskkill /f /im chrome.exe 2>nul || taskkill /f /im msedge.exe 2>nul",
        "name": "Браузер"
    },
    "chrome": {
        "keywords": ["гугл", "google", "хром", "chrome"],
        "open_cmd": "start chrome about:blank",
        "close_cmd": "taskkill /f /im chrome.exe 2>nul",
        "name": "Google Chrome"
    },
    "yandex": {
        "keywords": ["яндекс", "яндекс браузер", "yandex"],
        "open_cmd": "start https://ya.ru",
        "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul",
        "name": "Яндекс Браузер"
    },
    "ekursy": {
        "keywords": ["е-курсы", "е курсы", "курсы", "электронные курсы", "екурсы"],
        "open_cmd": "start https://e.sfu-kras.ru/",
        "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul || taskkill /f /im chrome.exe 2>nul || taskkill /f /im msedge.exe 2>nul",
        "name": "Е-курсы СФУ"
    },
    "schedule": {
        "keywords": ["расписание", "расписание сфу", "пары"],
        "open_cmd": "start https://edu.sfu-kras.ru/timetable#groups",
        "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul || taskkill /f /im chrome.exe 2>nul || taskkill /f /im msedge.exe 2>nul",
        "name": "Расписание СФУ"
    },
    "word": {
        "keywords": ["ворд", "word", "текстовый редактор", "текст"],
        "open_cmd": "start winword.exe",
        "close_cmd": "taskkill /f /im winword.exe 2>nul",
        "name": "Microsoft Word"
    },
    "powerpoint": {
        "keywords": ["повер поинт", "powerpoint", "презентация", "презентацию", "слайды"],
        "open_cmd": "start powerpnt.exe",
        "close_cmd": "taskkill /f /im powerpnt.exe 2>nul",
        "name": "Microsoft PowerPoint"
    },
}


# ====== ФУНКЦИИ ПАРСЕРА ======

def parse_command(text):
    """
    Разбирает распознанный текст и возвращает (intent, entity).
    """
    if text is None:
        return None, None

    found_intent = None
    found_entity = None

    # 1. Ищем намерение (действие)
    for intent, keywords in INTENTS.items():
        for keyword in keywords:
            if keyword in text:
                found_intent = intent
                break
        if found_intent:
            break

    # 2. Ищем объект (над чем действие)
    sorted_entities = sorted(
        ENTITIES.items(),
        key=lambda x: len(max(x[1]["keywords"], key=len)),
        reverse=True
    )
    for entity, data in sorted_entities:
        for keyword in data["keywords"]:
            if keyword in text:
                found_entity = entity
                break
        if found_entity:
            break

    return found_intent, found_entity


# ====== ПОТОК РАСПОЗНАВАНИЯ ======

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
            self.recognizer.energy_threshold = 500

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


# ====== ОБРАБОТЧИК КОМАНД ======

class VoiceCommandProcessor:
    """Обработчик голосовых и текстовых команд"""

    @staticmethod
    def _change_volume(delta):
        """Изменяет громкость через эмуляцию мультимедийных клавиш"""
        import keyboard
        if delta > 0:
            for _ in range(int(delta * 10)):
                keyboard.press_and_release('volume up')
        else:
            for _ in range(int(-delta * 10)):
                keyboard.press_and_release('volume down')

    @staticmethod
    def _mute():
        """Выключает звук — опускает громкость до нуля"""
        import keyboard
        for _ in range(50):
            keyboard.press_and_release('volume down')
            time.sleep(0.01)

    @staticmethod
    def _unmute():
        """Включает звук — поднимает громкость на 10%"""
        import keyboard
        for _ in range(5):
            keyboard.press_and_release('volume up')
            time.sleep(0.01)

    @staticmethod
    def _set_volume(level):
        """Устанавливает громкость на указанный уровень (0-100)"""
        import keyboard
        
        # Опускаем громкость до нуля
        for _ in range(50):
            keyboard.press_and_release('volume down')
            time.sleep(0.01)
        
        # Поднимаем до нужного уровня (1 нажатие ≈ 2%)
        presses = int(level / 2)
        for _ in range(presses):
            keyboard.press_and_release('volume up')
            time.sleep(0.01)

    @staticmethod
    def execute_command(text, callback_update=None):
        """
        Выполняет команду, используя умный парсер.
        """
        if text is None:
            return True

        intent, entity = parse_command(text)

        # === ОТКРЫТЬ ===
        if intent == "open" and entity:
            data = ENTITIES[entity]
            os.system(data["open_cmd"])
            if callback_update:
                callback_update(f"✅ {data['name']} открыт")
            return True

        # === ЗАКРЫТЬ ===
        if intent == "close" and entity:
            data = ENTITIES[entity]
            if data["close_cmd"]:
                os.system(data["close_cmd"])
                if callback_update:
                    callback_update(f"✅ {data['name']} закрыт")
            else:
                if callback_update:
                    callback_update(f"⚠️ {data['name']} нельзя закрыть принудительно")
            return True

        # === ГРОМЧЕ ===
        if intent == "volume_up":
            VoiceCommandProcessor._change_volume(0.5)
            if callback_update:
                callback_update("🔊 громкость увеличена")
            return True

        # === ТИШЕ ===
        if intent == "volume_down":
            VoiceCommandProcessor._change_volume(-0.5)
            if callback_update:
                callback_update("🔉 громкость уменьшена")
            return True

        # === ВЫКЛЮЧИТЬ ЗВУК ===
        if intent == "volume_mute":
            VoiceCommandProcessor._mute()
            if callback_update:
                callback_update("🔇 звук выключен")
            return True

        # === ВКЛЮЧИТЬ ЗВУК ===
        if intent == "volume_unmute":
            VoiceCommandProcessor._unmute()
            if callback_update:
                callback_update("🔊 звук включен")
            return True

        # === ГРОМКОСТЬ НА УРОВЕНЬ ===
        if intent == "volume_set":
            numbers = re.findall(r'\d+', text)
            if numbers:
                level = int(numbers[0])
                level = max(0, min(100, level))
                VoiceCommandProcessor._set_volume(level)
                if callback_update:
                    callback_update(f"🔊 громкость: {level}%")
            else:
                if callback_update:
                    callback_update("⚠️ не удалось определить уровень громкости")
            return True

        # === ВЫХОД ===
        if intent == "exit":
            if callback_update:
                callback_update("👋 выход из программы")
            return False

        # === НЕ РАСПОЗНАНО ===
        if callback_update:
            callback_update("команда не распознана")
        return True


# ====== КОНСОЛЬНЫЙ РЕЖИМ ======
if __name__ == "__main__":
    print("=" * 50)
    print("🎙️  ГОЛОСОВОЙ ПОМОЩНИК (консольный режим)")
    print("📋 Команды: открой/закрой блокнот, браузер, ворд, презентация, курсы, расписание")
    print("   громче/тише/выключи звук/включи звук, звук на 50, звук на полную, выход")
    print("=" * 50)

    recognizer = sr.Recognizer()
    running = True
    while running:
        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception:
                pass
            recognizer.energy_threshold = 500

            try:
                print("\n🎤 Слушаю...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio, language="ru-RU")
                print(f"📝 Распознано: {text}")
                intent, entity = parse_command(text.lower())
                print(f"   intent: {intent}, entity: {entity}")
                running = VoiceCommandProcessor.execute_command(text.lower())
                if running:
                    time.sleep(1)
            except sr.WaitTimeoutError:
                print("⏰ Ничего не сказано")
            except sr.UnknownValueError:
                print("❓ Не распознано")
            except sr.RequestError as e:
                print(f"🌐 Ошибка: {e}")  