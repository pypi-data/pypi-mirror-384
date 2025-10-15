import functools

from PyQt6.QtCore import Qt, QUrl, QTimer, QElapsedTimer, QObject, QEvent, qInstallMessageHandler, QPointF
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QLabel
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QShortcut, QKeySequence, QPixmap, QImage

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import parselmouth


class AudioViewer(QWidget):
    """
    Panel showing a Praat spectogram of the current sound, with a pitch track overlaid,
    a moving progress bar depending on the audioplayer position, and a moving bar corresponding
    to the cursor's x position in the window.
    """

    FRAMERATE = 60  # fps
    REFRESH_PERIOD = 1000 // FRAMERATE

    def __init__(self, player: AudioPlayer, parent=None, width_for_plot: float = 1.0):
        """
        The audioplayer matters for displaying a moving progress bar based on the audioplayer's (estimated) position.
        Width_for_plot [0,1] matters because it will affect the width of the textbubbles panel.
        Parent is passed into super().
        """
        super().__init__(parent)
        self.fig = Figure(figsize=(8,3))
        self.width_for_plot = width_for_plot

        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # To be instantiated once first audio file is loaded
        self.ax = None
        self.ax2 = None
        self.progress_line = None
        self.progress_line_delayed = None
        self.cursor_line = None
        self.duration = None
        self.background = None
        self.last_drawn_position = None
        self.last_drawn_position_delayed = None

        self.player = player

        self.update_timer = QTimer(self)
        self.update_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.update_timer.setInterval(self.REFRESH_PERIOD)
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start()

        # For caching the plot background for more efficient drawing (blitting):
        self.canvas.mpl_connect('draw_event', self._on_draw)

    def _on_draw(self, event) -> None:
        """
        Handler for the 'draw_event' to recache the background.
        Will run on the first draw and any subsequent window resizes.
        """
        if self.canvas.get_renderer():
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def load_file(self, path: str) -> None:
        """
        Loads an audio file, processes it with praat (parselmouth) to extract spectogram and pitch,
        uses matplotlib to create the corresponding overlaid plots, and initiates two vertical lines:
        progress bar and cursor x-position bar.
        """

        self.fig.clear()

        # TODO: Cache the actual background, not only the data.
        # self.background = self.cached_backgrounds.get(path)

        self.ax = self.fig.add_subplot(111)
        pitch, spec, xmin, xmax = self.make_spectogram_cached(path)
        self.duration = xmax

        self.draw_spectrogram(spec, ax=self.ax)
        self.ax2 = self.ax.twinx()
        self.draw_pitch(pitch, ax=self.ax2)
        self.ax.set_xlim(xmin, xmax)

        rectangle = ((1.0-self.width_for_plot)/2, 0.1, self.width_for_plot, 0.8)
        self.ax.set_position(rectangle)
        self.ax2.set_position(rectangle)

        self.progress_line = self.ax.axvline(0, color=(0.4, 0.4, 1.0), linewidth=2, animated=True)
        self.progress_line_delayed = self.ax.axvline(0, color=(0.7, 0.7, 1.0), linewidth=1, animated=True)
        self.cursor_line = self.ax.axvline(x=0, color="white", alpha=.6, linewidth=1)
        self.canvas.draw()

        self.last_drawn_position = None
        self.last_drawn_position_delayed = None


    def update_progress(self) -> None:
        """
        Called by a timer with FRAMERATE, to update the moving progress bar, with some jitter avoidance.
        """
        if self.player.duration_ms():
            pos = self.player.estimate_current_position()
            fraction = pos / self.player.duration_ms()

            if (pos_delayed := self.player.get_delayed_position()) is not None:
                fraction_delayed = pos_delayed / self.player.duration_ms()
            else:
                fraction_delayed = None

            self.set_progress(fraction, fraction_delayed)

    def set_progress(self, fraction: float, fraction_delayed: float = None) -> None:
        """
        Redraws the spectogram plot with the vertical progress bar at the given fraction of the x-axis,
        using blitting for efficiency. Called by update_progress. If fraction_delayed is provided, a secondary
        line will be drawn.
        """
        if self.background is None or self.progress_line is None:
            return

        x = fraction * self.duration
        if self.last_drawn_position is not None and (self.last_drawn_position - .1) < x < self.last_drawn_position:
            x = self.last_drawn_position  # avoid jitter:

        self.progress_line.set_xdata([x])
        self.last_drawn_position = x

        if fraction_delayed is not None:
            x_delayed = fraction_delayed * self.duration
            if self.last_drawn_position_delayed is not None and (self.last_drawn_position_delayed - .1) < x_delayed < self.last_drawn_position_delayed:
                x_delayed = self.last_drawn_position_delayed  # avoid jitter:
            self.progress_line_delayed.set_xdata([x_delayed])
            self.last_drawn_position_delayed = x_delayed

        if self.cursor_line is not None:
            self.ax.draw_artist(self.cursor_line)

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.cursor_line)
        self.ax.draw_artist(self.progress_line)
        if fraction_delayed is not None:
            self.ax.draw_artist(self.progress_line_delayed)
        self.canvas.blit(self.ax.bbox)
        QApplication.processEvents()

    def update_cursor_line(self, global_pos: QPointF) -> None:
        """
        Updates the cursor line for the plot. Gets a global position, to be called from outside the class
        (in this case a global CursorMonitor instance). Redraw not actually done here; only in set_progress.
        """
        if self.background is None or self.cursor_line is None:
            return
        local_pos = self.canvas.mapFromGlobal(global_pos)
        xdata, _ = self.ax.transData.inverted().transform((local_pos.x(), local_pos.y()))
        self.cursor_line.set_xdata([xdata])

    @staticmethod
    @functools.cache
    def make_spectogram_cached(path):
        """
        Wrapper around parselmouth spectogram and pitch extraction, to be able to
        cache it (per .wav file path).
        """
        snd = parselmouth.Sound(str(path))
        pitch = snd.to_pitch(None)
        pre = snd.copy()
        pre.pre_emphasize()
        spec = pre.to_spectrogram(window_length=0.03, maximum_frequency=8000)
        return pitch, spec, snd.xmin, snd.xmax

    @staticmethod
    def draw_spectrogram(spec, ax, dynamic_range=70):
        """
        From parselmouth spectogram to a matplotlib plot.
        """
        data = 10 * np.log10(np.maximum(spec.values, 1e-10))
        vmax = data.max()
        vmin = vmax - dynamic_range

        X, Y = spec.x_grid(), spec.y_grid()
        sg_db = 10 * np.log10(spec.values)
        ax.pcolormesh(X, Y, sg_db, vmin=sg_db.max() - dynamic_range, cmap='afmhot')
        ax.axis(ymin=spec.ymin, ymax=spec.ymax)

        ax.imshow(data, origin='lower', aspect='auto', cmap='gray', extent=[spec.xmin, spec.xmax, 0, spec.ymax], vmin=vmin, vmax=vmax)
        ax.set_ylabel('Frequency (Hz)')

    @staticmethod
    def draw_pitch(pitch, ax):
        """
        From parselmouth pitch track to a matplotlib plot.
        """
        pitch_values = pitch.selected_array['frequency']
        pitch_values[pitch_values==0] = np.nan
        times = pitch.xs()
        ax.plot(times, pitch_values, color='cyan')
        ax.set_ylabel('Pitch (Hz)')



class AudioViewerWithAutoScroll(QWidget):
    """
    Panel showing a Praat spectogram of the current sound, with a pitch track overlaid,
    a moving progress bar depending on the audioplayer position, and a moving bar corresponding
    to the cursor's x position in the window.
    """

    FRAMERATE = 30  # fps
    REFRESH_PERIOD = 1000 // FRAMERATE

    VIEW_WIDTH_SECONDS = 5  # TODO: per song, determine close-to-5-whole-seconds length that actually neatly divides duration.
    VIEW_MARGIN = .2  # as proportion of window width seconds

    def __init__(self, player: AudioPlayer, parent=None, width_for_plot: float = 1.0):
        """
        The audioplayer matters for displaying a moving progress bar based on the audioplayer's (estimated) position.
        Width_for_plot [0,1] matters because it will affect the width of the textbubbles panel.
        Parent is passed into super().
        """
        super().__init__(parent)
        self.fig = Figure(figsize=(8,3))
        self.width_for_plot = width_for_plot

        self.canvas = FigureCanvas(self.fig)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # To be instantiated once first audio file is loaded
        self.ax = None
        self.ax2 = None
        self.progress_line = None
        self.progress_line_delayed = None
        self.cursor_line = None
        self.duration = None
        self.background = None
        self.last_drawn_position = None
        self.last_drawn_position_delayed = None

        self.player = player

        self.update_timer = QTimer(self)
        self.update_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.update_timer.setInterval(self.REFRESH_PERIOD)
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start()

        # For caching the plot background for more efficient drawing (blitting):
        self.canvas.mpl_connect('draw_event', self._on_draw)

    def _on_draw(self, event) -> None:
        """
        Handler for the 'draw_event' to recache the background.
        Will run on the first draw and any subsequent window resizes.
        """
        if self.canvas.get_renderer():
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)

    def load_file(self, path: str) -> None:
        """
        Loads an audio file, processes it with praat (parselmouth) to extract spectogram and pitch,
        uses matplotlib to create the corresponding overlaid plots, and initiates two vertical lines:
        progress bar and cursor x-position bar.
        """

        self.fig.clear()

        # TODO: Cache the actual background, not only the data.
        # self.background = self.cached_backgrounds.get(path)

        self.ax = self.fig.add_subplot(111)
        pitch, spec, xmin, xmax = self.make_spectogram_cached(path)
        self.duration = xmax

        self.draw_spectrogram(spec, ax=self.ax)
        self.ax2 = self.ax.twinx()
        self.draw_pitch(pitch, ax=self.ax2)
        self.ax.set_xlim(0, min(self.VIEW_WIDTH_SECONDS, xmax))

        rectangle = ((1.0-self.width_for_plot)/2, 0.1, self.width_for_plot, 0.8)
        self.ax.set_position(rectangle)
        self.ax2.set_position(rectangle)

        self.progress_line = self.ax.axvline(0, color=(0.4, 0.4, 1.0), linewidth=2, animated=True)
        self.progress_line_delayed = self.ax.axvline(0, color=(0.7, 0.7, 1.0), linewidth=1, animated=True)
        self.cursor_line = self.ax.axvline(x=0, color="white", alpha=.6, linewidth=1)
        self.canvas.draw()

        self.last_drawn_position = None
        self.last_drawn_position_delayed = None


    def update_progress(self) -> None:
        """
        Called by a timer with FRAMERATE, to update the moving progress bar, with some jitter avoidance.
        """
        if self.player.duration_ms():
            pos = self.player.estimate_current_position()
            fraction = pos / self.player.duration_ms()

            if (pos_delayed := self.player.get_delayed_position()) is not None:
                fraction_delayed = pos_delayed / self.player.duration_ms()
            else:
                fraction_delayed = None

            self.set_progress(fraction, fraction_delayed)

    def set_progress(self, fraction: float, fraction_delayed: float = None) -> None:
        """
        Redraws the spectogram plot with the vertical progress bar at the given fraction of the x-axis,
        using blitting for efficiency. Called by update_progress. If fraction_delayed is provided, a secondary
        line will be drawn.
        """
        if self.background is None or self.progress_line is None:
            return

        x = fraction * self.duration
        if self.last_drawn_position is not None and (self.last_drawn_position - .1) < x < self.last_drawn_position:
            x = self.last_drawn_position  # avoid jitter:

        self.progress_line.set_xdata([x])
        self.last_drawn_position = x

        if fraction_delayed is not None:
            x_delayed = fraction_delayed * self.duration
            if self.last_drawn_position_delayed is not None and (self.last_drawn_position_delayed - .1) < x_delayed < self.last_drawn_position_delayed:
                x_delayed = self.last_drawn_position_delayed  # avoid jitter:
            self.progress_line_delayed.set_xdata([x_delayed])
            self.last_drawn_position_delayed = x_delayed

        if self.cursor_line is not None:
            self.ax.draw_artist(self.cursor_line)

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.cursor_line)
        self.ax.draw_artist(self.progress_line)
        if fraction_delayed is not None:
            self.ax.draw_artist(self.progress_line_delayed)
        self.canvas.blit(self.ax.bbox)

        left, right = self.ax.get_xlim()
        dist = right - left
        if not left + self.VIEW_MARGIN * dist <= x <= right - self.VIEW_MARGIN * dist:
            start = max(x - self.VIEW_MARGIN * dist, 0)
            end = min(start + self.VIEW_WIDTH_SECONDS, self.duration)
            if end - start < self.VIEW_WIDTH_SECONDS:
                start = max(end - self.VIEW_WIDTH_SECONDS, 0)
            if start == left and end == right:
                return
            self.ax.set_xlim(start, end)
            self.canvas.draw()  # full redraw (slower, but occasional)
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)

        QApplication.processEvents()


    def update_cursor_line(self, global_pos: QPointF) -> None:
        """
        Updates the cursor line for the plot. Gets a global position, to be called from outside the class
        (in this case a global CursorMonitor instance). Redraw not actually done here; only in set_progress.
        """
        if self.background is None or self.cursor_line is None:
            return
        local_pos = self.canvas.mapFromGlobal(global_pos)
        xdata, _ = self.ax.transData.inverted().transform((local_pos.x(), local_pos.y()))
        self.cursor_line.set_xdata([xdata])

    @staticmethod
    @functools.cache
    def make_spectogram_cached(path):
        """
        Wrapper around parselmouth spectogram and pitch extraction, to be able to
        cache it (per .wav file path).
        """
        snd = parselmouth.Sound(str(path))
        pitch = snd.to_pitch(None)
        pre = snd.copy()
        pre.pre_emphasize()
        spec = pre.to_spectrogram(window_length=0.05, time_step=0.02, frequency_step=50, maximum_frequency=2000)
        return pitch, spec, snd.xmin, snd.xmax

    @staticmethod
    def draw_spectrogram(spec, ax, dynamic_range=70):
        """
        From parselmouth spectogram to a matplotlib plot.
        """
        data = 10 * np.log10(np.maximum(spec.values, 1e-10))
        vmax = data.max()
        vmin = vmax - dynamic_range

        X, Y = spec.x_grid(), spec.y_grid()
        sg_db = 10 * np.log10(spec.values)
        ax.pcolormesh(X, Y, sg_db, vmin=sg_db.max() - dynamic_range, cmap='afmhot')
        ax.axis(ymin=spec.ymin, ymax=spec.ymax)

        ax.imshow(data, origin='lower', aspect='auto', cmap='gray', extent=[spec.xmin, spec.xmax, 0, spec.ymax], vmin=vmin, vmax=vmax)
        ax.set_ylabel('Frequency (Hz)')

    @staticmethod
    def draw_pitch(pitch, ax):
        """
        From parselmouth pitch track to a matplotlib plot.
        """
        pitch_values = pitch.selected_array['frequency']
        pitch_values[pitch_values==0] = np.nan
        times = pitch.xs()
        ax.plot(times, pitch_values, color='blue')
        # ax.set_ylim(0, 1000)
        ax.set_ylabel('Pitch (Hz)')

