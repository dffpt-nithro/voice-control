import sys
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSizePolicy,
    QSystemTrayIcon, QMenu, QAction, QStyle
)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot
from VoiceControl import (
    RecognitionThread, VoiceCommandProcessor, WakeWordListener,
    speak, stop_speaking, load_settings, save_settings, settings, t
)
import keyboard


class CommandWorker(QObject):
    status_update = pyqtSignal(str)
    command_finished = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, command_text, hide_window_callback=None, show_window_callback=None):
        super().__init__()
        self.command_text = command_text
        self.hide_window_callback = hide_window_callback
        self.show_window_callback = show_window_callback

    @pyqtSlot()
    def run(self):
        try:
            running = VoiceCommandProcessor.execute_command(
                self.command_text,
                callback_update=self._on_status,
                hide_window_callback=self.hide_window_callback,
                show_window_callback=self.show_window_callback
            )
            self.command_finished.emit(running)
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.command_finished.emit(True)

    def _on_status(self, message):
        self.status_update.emit(message)


class GlobalHotkeyListener(QObject):
    space_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = True
        self._space_held = False

    @pyqtSlot()
    def run(self):
        keyboard.on_press_key('space', self._on_press_space)
        keyboard.on_release_key('space', self._on_release_space)
        while self._running:
            QThread.msleep(100)

    def _on_press_space(self, event):
        if not self._space_held:
            self._space_held = True
            self.space_pressed.emit()

    def _on_release_space(self, event):
        self._space_held = False

    def stop(self):
        self._running = False
        keyboard.unhook_all()


class VoiceAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('form.ui', self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(420, 720)   # немного увеличил высоту для новой панели
        self.resize(420, 720)

        self.recognition_thread = None
        self.command_thread = None
        self.command_worker = None
        self.is_listening = False

        self.hotkey_thread = QThread()
        self.hotkey_listener = GlobalHotkeyListener()
        self.hotkey_listener.moveToThread(self.hotkey_thread)
        self.hotkey_listener.space_pressed.connect(self.toggle_voice_recognition)
        self.hotkey_thread.started.connect(self.hotkey_listener.run)

        # Используем глобальный settings из VoiceControl
        self.wake_word = settings.get("wake_word", "улитка")
        self.wake_thread = None
        self.wake_listener = None
        self.start_wake_listener()

        self.recordButton_3.setText("🎤")

        # Инициализация переключателей языка и mute
        self.init_settings_ui()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip("Voice Control")
        self.tray_menu = QMenu()
        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show_window)
        self.tray_menu.addAction(show_action)
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        self.init_connections()
        self.hotkey_thread.start()
        self.retranslate_ui()
        self.show()
        self.update_status(f"жду «{self.wake_word}»...")
        speak(t("greeting"))

    # ====== МГНОВЕННЫЙ ПЕРЕВОД ИНТЕРФЕЙСА ======
    def retranslate_ui(self):
        lang = settings.get("language", "ru")
        tr = lambda ru_text, en_text: ru_text if lang == "ru" else en_text

        self.setWindowTitle(tr("Voice Control", "Voice Control"))
        self.recordButtonLabel_2.setText(tr("нажмите и говорите", "press and speak"))
        self.commandInput_3.setPlaceholderText(tr("введите команду...", "type a command..."))
        self.commandInputLabel.setText(tr("ручной ввод команд", "manual command input"))
        self.tray_icon.setToolTip(tr("Voice Control", "Voice Control"))

        # Обновление пунктов трея
        if hasattr(self, 'tray_menu'):
            self.tray_menu.actions()[0].setText(tr("Показать", "Show"))
            self.tray_menu.actions()[1].setText(tr("Выход", "Exit"))

    def update_status(self, text):
        prefix = "распознано:" if settings.get("language", "ru") == "ru" else "recognized:"
        self.recognitionLabel_3.setText(f"{prefix} {text}")

    # ====== УПРАВЛЕНИЕ НАСТРОЙКАМИ ======
    def init_settings_ui(self):
        lang = settings.get("language", "ru")
        muted = settings.get("mute", False)

        self.langRuButton.setChecked(lang == "ru")
        self.langEnButton.setChecked(lang == "en")
        self.muteButton.setChecked(muted)
        self._update_mute_button_icon(muted)

        self.langRuButton.clicked.connect(self.on_lang_ru_clicked)
        self.langEnButton.clicked.connect(self.on_lang_en_clicked)
        self.muteButton.clicked.connect(self.on_mute_toggled)

    def _update_mute_button_icon(self, muted):
        self.muteButton.setText("🔇" if muted else "🔊")

    def on_lang_ru_clicked(self):
        if settings.get("language") != "ru":
            settings["language"] = "ru"
            save_settings(settings)
            self.langRuButton.setChecked(True)
            self.langEnButton.setChecked(False)
            self.retranslate_ui()
            self.update_status(t("lang_ru"))
            # speak(t("lang_ru"))   # если нужна голосовая обратная связь

    def on_lang_en_clicked(self):
        if settings.get("language") != "en":
            settings["language"] = "en"
            save_settings(settings)
            self.langRuButton.setChecked(False)
            self.langEnButton.setChecked(True)
            self.retranslate_ui()
            self.update_status(t("lang_en"))
            # speak(t("lang_en"))

    def on_mute_toggled(self):
        muted = not settings.get("mute", False)
        settings["mute"] = muted
        save_settings(settings)
        self._update_mute_button_icon(muted)
        if muted:
            stop_speaking()          # мгновенно останавливаем текущую озвучку
            self.update_status(t("muted"))
        else:
            self.update_status(t("unmuted"))

    # ====== ОСТАЛЬНЫЕ МЕТОДЫ БЕЗ ИЗМЕНЕНИЙ ======
    def start_wake_listener(self):
        if self.wake_listener:
            self.wake_listener.stop()
        if self.wake_thread:
            self.wake_thread.quit()
            self.wake_thread.wait()
        self.wake_listener = WakeWordListener(self.wake_word)
        self.wake_thread = QThread()
        self.wake_listener.moveToThread(self.wake_thread)
        self.wake_listener.wake_word_detected.connect(self.on_wake_word)
        self.wake_thread.started.connect(self.wake_listener.run)
        self.wake_thread.start()

    def on_wake_word(self):
        stop_speaking()
        self.play_sound()
        self.update_status("слушаю команду...")
        speak("Слушаю")
        self.start_voice_recognition()

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
                font-size: 32px; font-weight: bold;
            }
        """)
        self.recognition_thread = RecognitionThread()
        self.recognition_thread.text_recognized.connect(self.process_voice_command)
        self.recognition_thread.error_occurred.connect(self.on_recognition_error)
        self.recognition_thread.start()

    def stop_voice_recognition(self):
        self.is_listening = False
        if self.recognition_thread:
            self.recognition_thread.quit()
            self.recognition_thread.wait()
            self.recognition_thread = None
        self.update_status(f"жду «{self.wake_word}»...")
        self.recordButton_3.setText("🎤")
        self.recordButton_3.setStyleSheet("""
            QPushButton {
                background-color: #0a0a0a; color: #88ccff;
                border: 2px solid #66ccff; border-radius: 60px;
                font-size: 32px; font-weight: bold;
            }
        """)

    def process_voice_command(self, text):
        if not text:
            return
        self.start_command(text)

    def on_recognition_error(self, message):
        self.update_status(message)
        self.stop_voice_recognition()
        self.play_sound()

    def send_text_command(self):
        command = self.commandInput_3.text().strip()
        if not command:
            self.update_status("введите команду")
            return
        self.update_status(f"команда: {command}")
        self.commandInput_3.clear()
        self.start_command(command)

    def start_command(self, command_text):
        if self.is_listening:
            self.stop_voice_recognition()
        if self.command_thread and self.command_thread.isRunning():
            self.update_status("подождите...")
            return
        self.recordButton_3.setEnabled(False)
        self.sendCommandButton.setEnabled(False)
        self.commandInput_3.setEnabled(False)
        self.command_worker = CommandWorker(
            command_text,
            hide_window_callback=self.hide_for_reading,
            show_window_callback=self.show_window
        )
        self.command_thread = QThread()
        self.command_worker.moveToThread(self.command_thread)
        self.command_worker.status_update.connect(self.update_status)
        self.command_worker.command_finished.connect(self.on_command_finished)
        self.command_worker.error_occurred.connect(self.on_command_error)
        self.command_thread.started.connect(self.command_worker.run)
        self.command_worker.command_finished.connect(self.command_thread.quit)
        self.command_worker.error_occurred.connect(self.command_thread.quit)
        self.command_thread.finished.connect(self.cleanup_command_thread)
        self.command_thread.start()

    def hide_for_reading(self):
        self.hide()

    def on_command_finished(self, running):
        self.show()
        self.play_sound()
        if not running:
            self.quit_app()

    def on_command_error(self, error_msg):
        self.show()
        self.update_status(f"ошибка: {error_msg}")
        self.play_sound()

    def cleanup_command_thread(self):
        if self.command_worker:
            self.command_worker.deleteLater()
            self.command_worker = None
        if self.command_thread:
            self.command_thread.deleteLater()
            self.command_thread = None
        self.show()
        self.recordButton_3.setEnabled(True)
        self.sendCommandButton.setEnabled(True)
        self.commandInput_3.setEnabled(True)

    def play_sound(self):
        QApplication.beep()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Voice Control",
            "Программа работает в фоне",
            QSystemTrayIcon.Information,
            2000
        )

    def quit_app(self):
        if self.wake_listener:
            self.wake_listener.stop()
        if self.wake_thread:
            self.wake_thread.quit()
            self.wake_thread.wait()
        self.hotkey_listener.stop()
        self.hotkey_thread.quit()
        self.hotkey_thread.wait()
        self.tray_icon.hide()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = VoiceAssistant()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()