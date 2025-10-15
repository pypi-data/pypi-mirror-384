import sys
import os
import logging
import functools

from PyQt6.QtCore import Qt, QUrl, QTimer, QElapsedTimer, QObject, QEvent, qInstallMessageHandler, QPointF
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QLabel, QGraphicsView
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QShortcut, QKeySequence, QPainter, QKeyEvent

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import parselmouth

from .textbubbles import TextBubbleScene, TextBubble
from . import ui_helpers
from . import io
from .ui_helpers import Keys
from collections import deque


# TODO: Progress bar not correctly shown first 100-or-so ms.

class AudioPlayer(QMediaPlayer):
    """
    Wraps QMediaPlayer, mainly to facilitate displaying a more smoothly moving progress bar (because at least
    some audio back-ends may update position only once every 50-100ms), by virtue of self.estimate_current_position,
    as well as a delayed progress bar, by virtue of self.get_delayed_position
    """

    DELAY_MS = 500
    DELAY_REFRESH_PERIOD_MS = 10

    # UI things
    SEEK_STEP_MS = 800
    DELAY_DELTA_MS = 100  # increment size when adjusting delay

    def __init__(self, getposition_interval_ms=None):
        """
        Instantiates the audio player, connects it to the audio output, and sets up
        bookkeeping attributes for estimation of current position.

        If getposition_interval_ms is specified, will sync the queue with calls to estimate_current_position.
        """
        super().__init__()
        self.audio_output = QAudioOutput()  # apparently needed
        self.setAudioOutput(self.audio_output)

        # To 'extrapolate' current position for a smoother moving progress bar:
        self.elapsedtimer = QElapsedTimer()
        self.elapsedtimer.start()
        self.last_position = 0
        self.time_of_last_position = 0
        self.positionChanged.connect(self.on_position_changed)

        # Queue to store previous positions.
        self.sync_queue_with_getposition = getposition_interval_ms is not None
        if self.sync_queue_with_getposition:
            self.DELAY_REFRESH_PERIOD_MS = getposition_interval_ms
        self.position_queue_maxlength = self.DELAY_MS // self.DELAY_REFRESH_PERIOD_MS
        self.position_queue: deque[int] = deque()

        if not self.sync_queue_with_getposition:  # set up its own timer
            self.queue_refresh_timer = QTimer(self)
            self.queue_refresh_timer.setTimerType(Qt.TimerType.PreciseTimer)
            self.queue_refresh_timer.setInterval(self.DELAY_REFRESH_PERIOD_MS)
            self.queue_refresh_timer.timeout.connect(self.update_position_queue)
            self.queue_refresh_timer.start()

        self.update_position = False  # only set to True once position has been updated for the first time

    def load_file(self, path: str, autoplay=True) -> None:
        """
        Loads a file and (by default) starts playing.
        """
        self.setSource(QUrl.fromLocalFile(path))
        self.position_queue.clear()
        if autoplay:
            QTimer.singleShot(150, self.play)
            self.position_queue.appendleft(0)
            self.last_position = None
            self.update_position = False

    def toggle_play_pause(self) -> None:
        """
        For use by play/pause hotkey.
        """
        if self.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.time_of_last_position = None
            self.play()

    def seek_relative(self, delta_ms: int) -> None:
        """
        Skips sound player ahead by delta_ms (or back, if negative), capped between 0 and duration.
        """
        newpos = min(max(0, self.position() + delta_ms), self.duration())
        self.setPosition(newpos)
        self.position_queue.clear()
        self.position_queue.appendleft(newpos)
        self.last_position = None  # in order for estimate_current_position to start afresh

    def estimate_current_position(self) -> int:
        """
        Estimates current position from last position and time_of_last_position.
        (Because at least some audio back-ends update position only once every 50-100ms.)
        """
        if not self.update_position:
            if self.sync_queue_with_getposition:
                self.update_position_queue(0)
            return 0

        if self.last_position is None:  # e.g., at the start or if position was recently changed by seeking
            self.on_position_changed(self.position())
        if self.playbackState() == self.PlaybackState.PlayingState and self.time_of_last_position is not None:
            delta = self.elapsedtimer.elapsed() - self.time_of_last_position
        else:
            delta = 0
        estimated_position = self.last_position + delta

        if self.sync_queue_with_getposition:
            self.update_position_queue(estimated_position)

        return estimated_position

    def get_delayed_position(self) -> int | None:
        """

        """
        if self.position_queue and self.DELAY_MS != 0:
            return self.position_queue[-1]
        else:
            return None

    def update_position_queue(self, pos=None):

        while len(self.position_queue) >= self.position_queue_maxlength:
            self.position_queue.pop()
        self.position_queue.appendleft(pos if pos is not None else self.estimate_current_position())

    def on_position_changed(self, ms: float) -> None:
        """
        Keeping position and timing data for extrapolating, as done in self.best_current_position.
        """
        self.last_position = ms
        self.time_of_last_position = self.elapsedtimer.elapsed()
        self.update_position = True  # now it's at least somewhat accurate

    def change_delay(self, delta: int):
        self.DELAY_MS = max(self.DELAY_MS + delta, 0)
        self.position_queue_maxlength = max(self.DELAY_MS // self.DELAY_REFRESH_PERIOD_MS, 1)



class CurrentlyPressedKeysTracker(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pressed_keys = set()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and not event.isAutoRepeat():
            self.pressed_keys.add(event.key())
        elif event.type() == QEvent.Type.KeyRelease and not event.isAutoRepeat():
            self.pressed_keys.discard(event.key())
        return False  # don't block the event



class TextBubbleSceneView(QGraphicsView):
    """
    Completing the PyQt graphics hierarchy of a view, a scene, and the text bubbles it contains.
    Handles resizeEvent (passed on to scene.resizrEventFromView), and keypresses to the containing
    TextBubble objects (when focused).
    """

    def __init__(self, proportion_width: float = 1.0):
        """
        Sets a new TextBubbleScene as its viewed scene; sets its width to a specified
        proportion of the view.
        """
        self.proportion_width = proportion_width
        self.text_bubble_scene = TextBubbleScene()
        super().__init__(self.text_bubble_scene)
        self.calibrate_actual_width()
        self.scene().setSceneRect(0, 0, self.actual_width, 100)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.calibrate_actual_width()
        self.scene().resizeEventFromView(self.actual_width)

    def calibrate_actual_width(self):
        self.actual_width = self.proportion_width * self.viewport().width()

    def keyPressEvent(self, event: QKeyEvent):
        if any(item.hasFocus() for item in self.scene().items()):
            super().keyPressEvent(event)
        else:
            event.ignore()

    def textBubbles(self):
        return [item for item in self.scene().items() if isinstance(item, TextBubble)]

    def remove_all_bubbles(self):
        """
        Clears all annotation bubbles.
        """
        for bubble in self.textBubbles():
            bubble.scene().removeItem(bubble)

    def remove_last_added_bubble(self):
        """
        Removes the last added bubble, which happens to be the first one in self.scene.items().
        """
        bubbles = self.textBubbles()
        if bubbles:
            last_bubble = bubbles.pop(0)
            last_bubble.scene().removeItem(last_bubble)

    def load_file(self, path):
        pass

    def update_cursor_line(self, event):
        pass


class ToneSwiperWindow(QMainWindow):
    """
    Main window of the app, wrapping an AudioPlayer, Audioviewer and TextBubbleSceneView.
    Handles most keyboard controls for transcription and audioplayer.
    """

    def __init__(self, wavfiles: list[str], save_as_textgrids: str = None, save_as_json: str = None):
        """
        Takes a list of .wav files to be annotated, and optionally where to load/save annotations from
        (textgrids or json). Sets up window layout, loads the first sound file, and sets up some
        bookkeeping for registering key sequences.
        """
        super().__init__()
        self.wavfiles = wavfiles
        self.save_as_textgrid_tier = save_as_textgrids
        self.save_as_json = save_as_json

        self.currently_pressed_keys_tracker = CurrentlyPressedKeysTracker()

        self.transcriptions = [[] for _ in self.wavfiles]
        if self.save_as_json and os.path.exists(self.save_as_json):
            from_json = io.load_from_json(self.save_as_json)
            self.transcriptions = [from_json.get(filename, []) for filename in self.wavfiles]
            if self.save_as_textgrid_tier:
                logging.warning("Both save_as_json and save_as_textgrid_tier specified;"
                                "will only load from textgrids (but save to both).")
        if self.save_as_textgrid_tier:
            from_textgrids = io.load_from_textgrids(self.wavfiles, self.save_as_textgrid_tier)
            self.transcriptions = [from_textgrids.get(wavfile, []) for wavfile in self.wavfiles]

        self.setWindowTitle('ToneSwiper')
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        self.label = QLabel('', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QApplication.font()
        font.setPointSize(14)
        self.label.setFont(font)
        layout.addWidget(self.label)

        self.audioplayer = AudioPlayer()  # getposition_interval_ms=AudioViewer.REFRESH_PERIOD

        self.audioviewer = TextBubbleSceneView(proportion_width=0.8)
        # AudioViewer(self.audioplayer, self, width_for_plot=0.8)
        layout.addWidget(self.audioviewer)

        self.current_file_index = None
        self.load_sound_by_index(0)
        self.transcription_loaded = False

        # For registering ToDI transcription key sequences
        self.current_key_sequence = []
        self.current_key_sequence_time = None

    def load_sound_by_index(self, idx: int) -> None:
        """
        For an index to a sound file, this function stores current annotations in memory, loads and plays
        the requested sound file, and (re)loads the corresponding audioviewer (spectogram) and transcription
        panels (the latter only once the audio's duration is known).
        """
        self.keys_currently_pressed = set()    # to serve as refresh, sometimes it gets stuck...

        if idx == self.current_file_index:
            return

        if self.current_file_index is not None:  # i.e., if it's not first file, first save the current annotations
            if self.transcription_loaded:
                self.transcriptions[self.current_file_index] = [(b.relative_x * self.audioplayer.duration(), b.toPlainText()) for b in self.audioviewer.textBubbles()]
                for item in self.audioviewer.textBubbles():
                    item.scene().removeItem(item)

        self.transcription_loaded = False

        self.current_file_index = idx % len(self.wavfiles)
        path = self.wavfiles[self.current_file_index]
        self.label.setText(f"File {self.current_file_index + 1}/{len(self.wavfiles)}: {path}")

        self.audioviewer.load_file(path)
        self.audioplayer.stop()
        self.audioplayer.load_file(path)
        # Audioplayer may take a while to know the duration, which in turn affects the placement of annotations:
        self.audioplayer.durationChanged.connect(self.duration_known_so_load_transcription)

    def duration_known_so_load_transcription(self, duration):
        """
        Called once upon loading a new sound file, just to determine when the audioplayer is ready
        to determine the current file's duration -- needed for placing the annotation bubbles.
        """
        if duration > 0:
            for time, text in self.transcriptions[self.current_file_index]:
                self.audioviewer.text_bubble_scene.new_item_relx(time / self.audioplayer.duration(), text)
        self.audioplayer.durationChanged.disconnect()
        self.transcription_loaded = True

    def keyPressEvent(self, event):
        """
        Handles most keyboard inputs, as defined in the Keys class, for controlling the audioplayer and
        for making the annotations.
        """
        if event.isAutoRepeat():
            return

        key = event.key()

        if key in Keys.PAUSE:
            self.audioplayer.toggle_play_pause()
            return
        elif key in Keys.FORWARD:
            self.audioplayer.seek_relative(self.audioplayer.SEEK_STEP_MS)
        elif key in Keys.BACKWARD:
            self.audioplayer.seek_relative(-self.audioplayer.SEEK_STEP_MS)
        elif key in Keys.MOREDELAY:
            self.audioplayer.change_delay(self.audioplayer.DELAY_DELTA_MS)
        elif key in Keys.LESSDELAY:
            self.audioplayer.change_delay(-self.audioplayer.DELAY_DELTA_MS)
        elif key in Keys.SLOWER:
            self.audioplayer.setPlaybackRate(max(self.audioplayer.playbackRate() - 0.1, 0.5))
        elif key in Keys.FASTER:
            self.audioplayer.setPlaybackRate(min(self.audioplayer.playbackRate() + 0.1, 2.0))
        elif key in Keys.NEXT or (key == Qt.Key.Key_Right and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.next()
        elif key in Keys.PREVIOUS or (key == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.prev()
        elif key in Keys.HOME:
            self.load_sound_by_index(0)
        elif key in Keys.END:
            self.load_sound_by_index(len(self.wavfiles) - 1)

        if key == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.audioviewer.remove_all_bubbles()
            else:
                self.audioviewer.remove_last_added_bubble()
        elif key in Keys.TODI_KEYS:
            self.current_key_sequence.append(key)
            if key not in Keys.DOWNSTEP:
                self.current_key_sequence_time = self.audioplayer.get_delayed_position()
        else:
            self.current_key_sequence = []
            self.current_key_sequence_time = None

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """
        Key sequences are built up until no more keys are currently pressed. Then they are released and
        turned into a transcription, which if feasible results in a new text bubble in the transcription panel.
        """
        if event.isAutoRepeat():
            return

        if self.currently_pressed_keys_tracker.pressed_keys:  # Sequence not yet completed
            return

        if self.current_key_sequence and self.current_key_sequence_time:
            try:
                transcription = ui_helpers.key_sequence_to_transcription(self.current_key_sequence)
            except ValueError as e:
                logging.warning(e)
            else:
                self.audioviewer.text_bubble_scene.new_item_relx(self.current_key_sequence_time / self.audioplayer.duration(), transcription)

        self.current_key_sequence = []
        self.current_key_sequence_time = None

    def next(self):
        """
        Go to next audio file (modulo-ized).
        """
        self.load_sound_by_index((self.current_file_index + 1) % len(self.wavfiles))

    def prev(self):
        """
        Go to previous audio file (modulo-ized).
        """
        self.load_sound_by_index((self.current_file_index - 1) % len(self.wavfiles))

    def closeEvent(self, event):
        """
        Upon closing the window, current transcription bubbles are stored in memory,
        and all transcriptions in memory are then saved either as a textgrid, or as json.
        """
        self.transcriptions[self.current_file_index] = [(b.relative_x * self.audioplayer.duration(), b.toPlainText()) for b in self.audioviewer.textBubbles()]

        self.audioplayer.stop()

        if self.save_as_textgrid_tier:
            io.write_to_textgrids(self.transcriptions,
                                  [wavfile.replace('.wav', '.TextGrid') for wavfile in self.wavfiles],
                                  self.audioplayer.duration(),
                                  self.save_as_textgrid_tier)
        else:
            io.write_to_json(self.wavfiles, self.transcriptions, to_file=self.save_as_json)

        event.accept()


def main():
    """
    Starts the PyQt6 app and main window, and calls upon various ui_helpers for intercepting tab/shift+tab,
    mouse movements, mute some log messages, and sets up F1 for help window.
    """

    args = ui_helpers.parse_args()

    app = QApplication(sys.argv)
    app.setStyle('fusion')
    icon = ui_helpers.load_icon()

    qInstallMessageHandler(ui_helpers.custom_message_handler)

    window = ToneSwiperWindow(args.files, save_as_textgrids=args.textgrid, save_as_json=args.json)
    app.setWindowIcon(icon)
    window.setWindowIcon(icon)

    tab_interceptor = ui_helpers.TabInterceptor(window.audioviewer.text_bubble_scene.handle_tabbing)
    app.installEventFilter(tab_interceptor)
    cursor_monitor = ui_helpers.CursorMonitor(window.audioviewer.update_cursor_line)
    app.installEventFilter(cursor_monitor)

    help_box = ui_helpers.HelpOverlay(window)
    QShortcut(QKeySequence("F1"), window, activated=help_box.display_panel)
    screen_geom = QApplication.primaryScreen().availableGeometry()
    help_box.move(screen_geom.right() - help_box.width(), screen_geom.top())

    window.resize(1200, 600)
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
