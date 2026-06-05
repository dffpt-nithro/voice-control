import speech_recognition as sr
import os
import time
import re
import json
import threading
from PyQt5.QtCore import QThread, pyqtSignal


# ====== НАСТРОЙКИ ======

SETTINGS_FILE = "settings.json"

def load_settings():
    default = {"wake_word": "улитка", "language": "ru"}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            default.update(data)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return default

def save_settings(settings_dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, ensure_ascii=False, indent=2)

settings = load_settings()


# ====== ОЗВУЧКА ======

_tts_engine = None
_stop_flag = False

def speak(text):
    global _tts_engine, _stop_flag
    _stop_flag = False
    lang = settings.get("language", "ru")
    target = speak_ru if lang == "ru" else speak_en
    threading.Thread(target=target, args=(text,), daemon=True).start()

def speak_ru(text):
    global _tts_engine, _stop_flag
    try:
        import pyttsx3
        _tts_engine = pyttsx3.init()
        voices = _tts_engine.getProperty('voices')
        for voice in voices:
            if any(x in voice.name.lower() for x in ['russian', 'русский', 'irina', 'microsoft ru', 'tts_ms_ru']):
                _tts_engine.setProperty('voice', voice.id)
                break
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception:
        pass
    finally:
        _tts_engine = None

def speak_en(text):
    global _tts_engine, _stop_flag
    try:
        import pyttsx3
        _tts_engine = pyttsx3.init()
        voices = _tts_engine.getProperty('voices')
        for voice in voices:
            if any(x in voice.name.lower() for x in ['zira', 'david', 'mark', 'english']):
                _tts_engine.setProperty('voice', voice.id)
                break
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception:
        pass
    finally:
        _tts_engine = None

def stop_speaking():
    global _tts_engine
    if _tts_engine:
        try:
            _tts_engine.stop()
        except Exception:
            pass


# ====== РЕПЛИКИ ======

def t(key):
    phrases = {
        "greeting": {"ru": "Привет! Я улитка, слушаю вас.", "en": "Hello! I'm Snail, listening to you."},
        "listening": {"ru": "Слушаю", "en": "Listening"},
        "searching": {"ru": "Ищу в интернете", "en": "Searching the web"},
        "typing": {"ru": "Печатаю", "en": "Typing"},
        "reading": {"ru": "Читаю экран", "en": "Reading screen"},
        "opening": {"ru": "Открываю", "en": "Opening"},
        "closing": {"ru": "Закрываю", "en": "Closing"},
        "louder": {"ru": "Громче", "en": "Louder"},
        "quieter": {"ru": "Тише", "en": "Quieter"},
        "muted": {"ru": "Звук выключен", "en": "Muted"},
        "unmuted": {"ru": "Звук включен", "en": "Unmuted"},
        "volume_set": {"ru": "Громкость", "en": "Volume"},
        "percent": {"ru": "процентов", "en": "percent"},
        "goodbye": {"ru": "До свидания", "en": "Goodbye"},
        "not_recognized": {"ru": "команда не распознана", "en": "command not recognized"},
        "waiting": {"ru": "жду", "en": "waiting for"},
        "lang_ru": {"ru": "🇷🇺 язык: русский", "en": "🇷🇺 Language: Russian"},
        "lang_en": {"ru": "🇬🇧 язык: английский", "en": "🇬🇧 Language: English"},
        "cannot_close": {"ru": "нельзя закрыть принудительно", "en": "cannot force close"},
        "opened": {"ru": "открыт", "en": "opened"},
        "closed": {"ru": "закрыт", "en": "closed"},
        "speak_command": {"ru": "слушаю команду...", "en": "listening for command..."},
        "dictation_start": {"ru": "🎙️ говорите... скажите «стоп» когда закончите", "en": "🎙️ speak... say «stop» when finished"},
        "dictation_stop": {"ru": "⏹ остановлено", "en": "⏹ stopped"},
        "printed": {"ru": "⌨️ текст напечатан", "en": "⌨️ text printed"},
        "click_window": {"ru": "🎙️ кликните в окно для ввода...", "en": "🎙️ click on the window for input..."},
        "search_query": {"ru": "🔍 ищу", "en": "🔍 searching for"},
        "nothing_found": {"ru": "❌ Ничего не найдено", "en": "❌ Nothing found"},
        "say_what_find": {"ru": "⚠️ скажите, что найти", "en": "⚠️ say what to find"},
        "found_entity": {"ru": "Найдено", "en": "Found"},
        "can_open_close": {"ru": "Можете открыть или закрыть", "en": "You can open or close it"},
        "no_text": {"ru": "📖 ничего не выделено", "en": "📖 nothing selected"},
        "text_read": {"ru": "📖 зачитано", "en": "📖 read"},
    }
    lang = settings.get("language", "ru")
    return phrases.get(key, {}).get(lang, phrases.get(key, {}).get("ru", key))

def get_entity_name(entity_data):
    lang = settings.get("language", "ru")
    if isinstance(entity_data.get("name"), dict):
        return entity_data["name"].get(lang, entity_data["name"].get("ru", ""))
    return entity_data.get("name", "")


# ====== СЛОВАРИ КОМАНД ======

INTENTS = {
    "read": ["читай", "прочитай", "озвучь", "read", "read aloud", "speak screen"],
    "language": ["смени язык", "поменяй язык", "говори на", "язык на", "говори по", "переключи язык", "change language", "switch language", "speak in", "русский", "russian", "английский", "english"],
    "volume_unmute": ["включи звук", "включить звук", "верни звук", "со звуком", "unmute", "turn on sound", "sound on", "restore sound"],
    "volume_mute": ["выключи звук", "отключи звук", "mute", "без звука", "turn off sound", "sound off", "silence", "mute audio"],
    "volume_up": ["громче", "погромче", "прибавь громкость", "увеличь громкость", "повысь громкость", "volume up", "louder", "increase volume", "turn up"],
    "volume_down": ["тише", "потише", "убавь громкость", "уменьши громкость", "понизь громкость", "volume down", "quieter", "decrease volume", "turn down"],
    "volume_set": ["звук на", "громкость на", "поставь звук", "поставь громкость", "сделай звук", "сделай громкость", "уровень звука", "уровень громкости", "volume", "громкость", "set volume", "sound to", "volume to"],
    "search": ["ищи", "поищи", "поиск", "search", "find", "google", "look up", "найди в интернете", "поищи в интернете"],
    "type": ["пиши", "напиши", "введи", "печатай", "type", "write", "input"],
    "open": ["открой", "открыть", "запусти", "запустить", "включи", "включить", "вруби", "start", "open", "launch", "run", "execute", "найди", "найти"],
    "close": ["закрой", "закрыть", "выключи", "выключить", "убери", "сверни", "stop", "close", "kill", "terminate", "exit app"],
    "exit": ["выход", "выйди", "закрой программу", "закрыть программу", "стоп", "хватит", "exit", "quit", "shut down", "power off"],
}

ENTITIES = {
    "notepad": {"keywords": ["блокнот", "notepad", "text editor"], "open_cmd": "start notepad.exe", "close_cmd": "taskkill /f /im notepad.exe 2>nul", "name": {"ru": "Блокнот", "en": "Notepad"}},
    "calculator": {"keywords": ["калькулятор", "calculator", "calc"], "open_cmd": "start calc.exe", "close_cmd": 'powershell -command "Get-Process | Where-Object {$_.ProcessName -like \'*calc*\'} | Stop-Process -Force"', "name": {"ru": "Калькулятор", "en": "Calculator"}},
    "browser": {"keywords": ["браузер", "browser", "интернет", "internet"], "open_cmd": "cmd /c start https://ya.ru", "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul || taskkill /f /im chrome.exe 2>nul || taskkill /f /im msedge.exe 2>nul", "name": {"ru": "Браузер", "en": "Browser"}},
    "chrome": {"keywords": ["гугл", "google", "хром", "chrome"], "open_cmd": "start chrome about:blank", "close_cmd": "taskkill /f /im chrome.exe 2>nul", "name": {"ru": "Google Chrome", "en": "Google Chrome"}},
    "yandex": {"keywords": ["яндекс", "яндекс браузер", "yandex", "yandex browser"], "open_cmd": "start https://ya.ru", "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul", "name": {"ru": "Яндекс Браузер", "en": "Yandex Browser"}},
    "ekursy": {"keywords": ["е-курсы", "е курсы", "курсы", "электронные курсы", "екурсы", "e-courses", "courses"], "open_cmd": "start https://e.sfu-kras.ru/", "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul || taskkill /f /im chrome.exe 2>nul || taskkill /f /im msedge.exe 2>nul", "name": {"ru": "Е-курсы СФУ", "en": "E-courses"}},
    "schedule": {"keywords": ["расписание", "расписание сфу", "пары", "schedule", "timetable"], "open_cmd": "start https://edu.sfu-kras.ru/timetable#groups", "close_cmd": "taskkill /f /im browser.exe 2>nul || taskkill /f /im yandex.exe 2>nul || taskkill /f /im chrome.exe 2>nul || taskkill /f /im msedge.exe 2>nul", "name": {"ru": "Расписание СФУ", "en": "Schedule"}},
    "word": {"keywords": ["ворд", "word", "текстовый редактор", "текст", "microsoft word", "winword"], "open_cmd": "start winword.exe", "close_cmd": "taskkill /f /im winword.exe 2>nul", "name": {"ru": "Microsoft Word", "en": "Microsoft Word"}},
    "powerpoint": {"keywords": ["повер поинт", "powerpoint", "презентация", "презентацию", "слайды", "slides", "presentation"], "open_cmd": "start powerpnt.exe", "close_cmd": "taskkill /f /im powerpnt.exe 2>nul", "name": {"ru": "Microsoft PowerPoint", "en": "Microsoft PowerPoint"}},
}


# ====== ФУНКЦИИ ПАРСЕРА ======

def parse_command(text):
    if text is None:
        return None, None
    found_intent = None
    found_entity = None
    for intent, keywords in INTENTS.items():
        for keyword in keywords:
            if keyword in text:
                found_intent = intent
                break
        if found_intent:
            break
    sorted_entities = sorted(ENTITIES.items(), key=lambda x: len(max(x[1]["keywords"], key=len)), reverse=True)
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


# ====== ФОНОВЫЙ СЛУШАТЕЛЬ ======

class WakeWordListener(QThread):
    wake_word_detected = pyqtSignal()
    def __init__(self, wake_word="улитка"):
        super().__init__()
        self.wake_word = wake_word.lower()
        self.is_running = False
        self.recognizer = sr.Recognizer()
    def run(self):
        self.is_running = True
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception:
                pass
            self.recognizer.energy_threshold = 500
            while self.is_running:
                try:
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                    text = self.recognizer.recognize_google(audio, language="ru-RU")
                    if self.wake_word in text.lower():
                        self.wake_word_detected.emit()
                        time.sleep(2)
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception:
                    pass
    def stop(self):
        self.is_running = False


# ====== ОБРАБОТЧИК КОМАНД ======

class VoiceCommandProcessor:

    @staticmethod
    def _change_volume(delta):
        import keyboard
        if delta > 0:
            for _ in range(int(delta * 10)):
                keyboard.press_and_release('volume up')
        else:
            for _ in range(int(-delta * 10)):
                keyboard.press_and_release('volume down')

    @staticmethod
    def _mute():
        import keyboard
        for _ in range(50):
            keyboard.press_and_release('volume down')
            time.sleep(0.01)

    @staticmethod
    def _unmute():
        import keyboard
        for _ in range(5):
            keyboard.press_and_release('volume up')
            time.sleep(0.01)

    @staticmethod
    def _set_volume(level):
        import keyboard
        for _ in range(50):
            keyboard.press_and_release('volume down')
            time.sleep(0.01)
        presses = int(level / 2)
        for _ in range(presses):
            keyboard.press_and_release('volume up')
            time.sleep(0.01)

    @staticmethod
    def _type_text(text, callback_update=None):
        import keyboard, pyperclip
        for keyword in INTENTS["type"]:
            if keyword in text:
                text = text.replace(keyword, "", 1).strip()
                break
        if text:
            pyperclip.copy(text)
            time.sleep(0.1)
            keyboard.press_and_release('ctrl+v')
            return
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        first_phrase = True
        with mic as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception:
                pass
            recognizer.energy_threshold = 500
            recognizer.pause_threshold = 2.0
            if callback_update:
                callback_update(t("click_window"))
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=60)
                    text = recognizer.recognize_google(audio, language="ru-RU").strip()
                    if text.lower() in ["стоп", "stop", "хватит", "всё", "все", "конец", "закончить"]:
                        if callback_update:
                            callback_update(t("dictation_stop"))
                        break
                    if first_phrase:
                        time.sleep(3)
                        first_phrase = False
                    pyperclip.copy(text + ". ")
                    keyboard.press_and_release('ctrl+v')
                    time.sleep(0.5)
                    if callback_update:
                        callback_update(f"📝 {text}")
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception:
                    break

    @staticmethod
    def _search_web(text, callback_update=None):
        import webbrowser
        for keyword in INTENTS["search"]:
            if keyword in text:
                text = text.replace(keyword, "", 1).strip()
                break
        if text:
            query = text.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            if callback_update:
                callback_update(f"{t('search_query')}: {text}")
            return
        recognizer = sr.Recognizer()
        all_parts = []
        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception:
                pass
            recognizer.energy_threshold = 500
            if callback_update:
                callback_update(t("dictation_start"))
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=30)
                    text = recognizer.recognize_google(audio, language="ru-RU").strip()
                    if text.lower() in ["стоп", "stop", "хватит", "всё", "все", "конец", "закончить"]:
                        if callback_update:
                            callback_update(t("dictation_stop"))
                        break
                    all_parts.append(text)
                    if callback_update:
                        callback_update(f"📝 {text}")
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception:
                    break
        if all_parts:
            query = " ".join(all_parts).replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={query}")
            if callback_update:
                callback_update(f"{t('search_query')}: {' '.join(all_parts)}")

    @staticmethod
    def _find_file(text, callback_update=None):
        import subprocess
        for keyword in INTENTS["open"]:
            if keyword in text:
                text = text.replace(keyword, "", 1).strip()
                break
        if not text:
            if callback_update:
                callback_update(t("say_what_find"))
            return None
        query = text.lower()
        query_clean = query.replace(" ", "_")
        try:
            result = subprocess.run(f'where "{query}*"', shell=True, capture_output=True, text=True, timeout=5)
            if result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                name = os.path.basename(path).rsplit('.', 1)[0]
                ENTITIES[query_clean] = {"keywords": [query], "open_cmd": f'start "" "{path}"', "close_cmd": f'taskkill /f /im "{os.path.basename(path)}" 2>nul', "name": {"ru": name, "en": name}}
                if callback_update:
                    callback_update(f"✅ {t('found_entity')}: {name}. {t('can_open_close')}.")
                return query_clean
        except Exception:
            pass
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        found = VoiceCommandProcessor._search_in_dir(desktop, query)
        if found:
            name = os.path.basename(found).rsplit('.', 1)[0]
            ENTITIES[query_clean] = {"keywords": [query], "open_cmd": f'start "" "{found}"', "close_cmd": f'taskkill /f /im "{os.path.basename(found)}" 2>nul', "name": {"ru": name, "en": name}}
            if callback_update:
                callback_update(f"✅ {t('found_entity')}: {name}. {t('can_open_close')}.")
            return query_clean
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        found = VoiceCommandProcessor._search_in_dir(documents, query)
        if found:
            name = os.path.basename(found).rsplit('.', 1)[0]
            ENTITIES[query_clean] = {"keywords": [query], "open_cmd": f'start "" "{found}"', "close_cmd": f'taskkill /f /im "{os.path.basename(found)}" 2>nul', "name": {"ru": name, "en": name}}
            if callback_update:
                callback_update(f"✅ {t('found_entity')}: {name}. {t('can_open_close')}.")
            return query_clean
        for prog_dir in ["C:\\Program Files", "C:\\Program Files (x86)"]:
            try:
                for entry in os.listdir(prog_dir):
                    if query in entry.lower():
                        full_dir = os.path.join(prog_dir, entry)
                        if os.path.isdir(full_dir):
                            for sub_entry in os.listdir(full_dir):
                                if sub_entry.lower().endswith('.exe') and query in sub_entry.lower():
                                    path = os.path.join(full_dir, sub_entry)
                                    ENTITIES[query_clean] = {"keywords": [query], "open_cmd": f'start "" "{path}"', "close_cmd": f'taskkill /f /im "{os.path.basename(path)}" 2>nul', "name": {"ru": entry, "en": entry}}
                                    if callback_update:
                                        callback_update(f"✅ {t('found_entity')}: {entry}. {t('can_open_close')}.")
                                    return query_clean
            except Exception:
                pass
        if callback_update:
            callback_update(f"{t('nothing_found')}: {text}")
        return None

    @staticmethod
    def _search_in_dir(directory, query):
        try:
            for entry in os.listdir(directory):
                if query in entry.lower():
                    return os.path.join(directory, entry)
            for entry in os.listdir(directory):
                full_path = os.path.join(directory, entry)
                if os.path.isdir(full_path):
                    for sub_entry in os.listdir(full_path):
                        if query in sub_entry.lower():
                            return os.path.join(full_path, sub_entry)
        except Exception:
            pass
        return None

    @staticmethod
    def _read_screen(callback_update=None, hide_window_callback=None):
        try:
            import uiautomation as auto
        except ImportError:
            if callback_update:
                callback_update("⚠️ uiautomation не установлен")
            return
        if hide_window_callback:
            hide_window_callback()
        time.sleep(0.3)
        try:
            control = auto.GetFocusedControl()
            text = ""
            try:
                text_pattern = control.GetTextPattern()
                if text_pattern:
                    selection = text_pattern.GetSelection()
                    if selection:
                        for sel in selection:
                            text += sel.GetText() + " "
            except Exception:
                pass
            if not text.strip():
                try:
                    value_pattern = control.GetValuePattern()
                    if value_pattern:
                        text = value_pattern.Value or ""
                except Exception:
                    pass
            if not text.strip():
                try:
                    parent = control.GetParentControl()
                    if parent:
                        text_pattern = parent.GetTextPattern()
                        if text_pattern:
                            selection = text_pattern.GetSelection()
                            if selection:
                                for sel in selection:
                                    text += sel.GetText() + " "
                except Exception:
                    pass
            text = text.strip()
            if not text:
                if callback_update:
                    callback_update(t("no_text"))
                return
            speak(text)
            if callback_update:
                callback_update(t("text_read"))
        except Exception as e:
            if callback_update:
                callback_update(f"⚠️ не удалось прочитать: {e}")

    @staticmethod
    def _set_language(text, callback_update=None):
        if any(w in text for w in ["английский", "англ", "english", "английски"]):
            settings["language"] = "en"
            save_settings(settings)
            if callback_update:
                callback_update(t("lang_en"))
            speak("Language set to English")
        elif any(w in text for w in ["русский", "рус", "russian", "по-русски"]):
            settings["language"] = "ru"
            save_settings(settings)
            if callback_update:
                callback_update(t("lang_ru"))
            speak("Язык изменён на русский")
        else:
            if callback_update:
                callback_update("⚠️ скажите: русский или английский")

    @staticmethod
    def execute_command(text, callback_update=None, hide_window_callback=None):
        if text is None:
            return True
        intent, entity = parse_command(text)

        if intent == "read":
            VoiceCommandProcessor._read_screen(callback_update, hide_window_callback)
            return True
        if intent == "language":
            VoiceCommandProcessor._set_language(text, callback_update)
            return True
        if intent == "search":
            VoiceCommandProcessor._search_web(text, callback_update)
            return True
        if intent == "type":
            VoiceCommandProcessor._type_text(text, callback_update)
            return True
        if intent == "open" and not entity:
            entity_key = VoiceCommandProcessor._find_file(text, callback_update)
            if entity_key and entity_key in ENTITIES:
                data = ENTITIES[entity_key]
                os.system(data["open_cmd"])
                name = get_entity_name(data)
                if callback_update:
                    callback_update(f"✅ {name} {t('opened')}")
                speak(f"{t('opening')} {name}")
            return True
        if intent == "open" and entity:
            data = ENTITIES[entity]
            os.system(data["open_cmd"])
            name = get_entity_name(data)
            if callback_update:
                callback_update(f"✅ {name} {t('opened')}")
            speak(f"{t('opening')} {name}")
            return True
        if intent == "close" and entity:
            data = ENTITIES[entity]
            name = get_entity_name(data)
            if data["close_cmd"]:
                os.system(data["close_cmd"])
                if callback_update:
                    callback_update(f"✅ {name} {t('closed')}")
                speak(f"{t('closing')} {name}")
            else:
                if callback_update:
                    callback_update(f"⚠️ {name} {t('cannot_close')}")
            return True
        if intent == "volume_up":
            VoiceCommandProcessor._change_volume(0.5)
            if callback_update:
                callback_update("🔊 " + t("louder"))
            speak(t("louder"))
            return True
        if intent == "volume_down":
            VoiceCommandProcessor._change_volume(-0.5)
            if callback_update:
                callback_update("🔉 " + t("quieter"))
            speak(t("quieter"))
            return True
        if intent == "volume_mute":
            VoiceCommandProcessor._mute()
            if callback_update:
                callback_update("🔇 " + t("muted"))
            speak(t("muted"))
            return True
        if intent == "volume_unmute":
            VoiceCommandProcessor._unmute()
            if callback_update:
                callback_update("🔊 " + t("unmuted"))
            speak(t("unmuted"))
            return True
        if intent == "volume_set":
            numbers = re.findall(r'\d+', text)
            if numbers:
                level = int(numbers[0])
                level = max(0, min(100, level))
                VoiceCommandProcessor._set_volume(level)
                if callback_update:
                    callback_update(f"🔊 {t('volume_set')}: {level}%")
                speak(f"{t('volume_set')} {level} {t('percent')}")
            return True
        if intent == "exit":
            if callback_update:
                callback_update("👋 " + t("goodbye"))
            speak(t("goodbye"))
            return False
        if callback_update:
            callback_update(t("not_recognized"))
        return True