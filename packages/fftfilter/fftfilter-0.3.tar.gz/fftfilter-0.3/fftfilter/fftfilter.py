#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Luis Bonah
# Description: Use FFT Filtering to remove periodic baselines from measurements

import os
import sys
import json
import glob
import argparse
import traceback as tb
import numpy as np
import pandas as pd
import threading
import matplotlib
import matplotlib.figure
import matplotlib.widgets

from matplotlib.backends.backend_qtagg import FigureCanvas, NavigationToolbar2QT
import scipy.fftpack

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

QLocale.setDefault(QLocale("en_EN"))

homefolder = os.path.join(os.path.expanduser("~"), ".fftfilter")
if not os.path.isdir(homefolder):
	os.mkdir(homefolder)

OPTIONFILE = os.path.join(homefolder, "default.json")
PYQT_MAX = 2147483647

matplotlib.rcParams['axes.formatter.useoffset'] = False
matplotlib.rcParams['patch.facecolor'] = "blue"


def high_pass_filter(omega, omega_down, n=5):
	if omega_down <= 0:
		return(np.ones(omega.shape))

	mask = (omega == 0)
	results = omega.copy()
	results[mask] = 0
	results[~mask] = 1 / (1 + (omega_down/omega[~mask]) ** (2*n))
	
	return(results)

def calculate_y_limits(ys, margin):
	ymin = np.nanmin(ys)
	ymax = np.nanmax(ys)
	ydiff = ymax-ymin
	
	return((ymin - margin * ydiff, ymax + margin * ydiff))




### GUI
class QSpinBox(QSpinBox):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setRange(0, PYQT_MAX)
		
	def setRange(self, min, max):
		min = min if not min is None else -np.inf
		max = max if not max is None else +np.inf
		return super().setRange(min, max)

class QDoubleSpinBox(QDoubleSpinBox):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setDecimals(20)
		self.setRange(0, PYQT_MAX)
		
		try:
			self.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
		except:
			pass

	def textFromValue(self, value):
		return(f"{value:.10f}".rstrip("0").rstrip("."))

	def valueFromText(self, text):
		return(np.float64(text))

	def setRange(self, min, max):
		min = min if not min is None else -np.inf
		max = max if not max is None else +np.inf
		return super().setRange(min, max)



class MainWindow(QMainWindow):
	updateconfig = pyqtSignal(tuple)
	redrawplot = pyqtSignal()
	
	def __init__(self, parent=None, **kwargs):
		global config
		
		super().__init__(parent)
		self.setAcceptDrops(True)
		self.timer = None
		self.update_data_thread = None
		self.update_data_lock = threading.RLock()
		
		self.data = None
		self.ys_corr = None
		self.files = None
		self.fileindex = 0

		config = self.config = Config(self.updateconfig, {
			'cutoff_freq': 0,
			'highpass': 0,
			'margin': 0.1,

			'mpltoolbar': True,
			'savefigure_kwargs': {
				"dpi": 600,
			},
			"asksavename": False,
			"savefile_kwargs": {
				"delimiter": "\t",
			},
		})

		self.gui()
		self.setWindowTitle("FFT Filtering")
		self.readoptions(OPTIONFILE, ignore=True)
		
		files = kwargs.get('files')
		if files:
			self.open_files(files)
		
		self.show()

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		files = [url.toLocalFile() for url in event.mimeData().urls()]
		self.open_files(files)

	def gui_menu(self):
		filemenu = self.menuBar().addMenu(f"File")

		filemenu.addAction(QQ(QAction, parent=self, text="&Open Files", shortcut="Ctrl+O", tooltip="Load files", change=lambda x: self.open_files()))
		filemenu.addSeparator()
		filemenu.addAction(QQ(QAction, parent=self, text="&Load Options", tooltip="Load option file", change=lambda x: self.readoptions()))
		filemenu.addAction(QQ(QAction, parent=self, text="&Save Options", tooltip="Save options to file", change=lambda x: self.saveoptions()))
		filemenu.addSeparator()
		filemenu.addAction(QQ(QAction, parent=self, text="&Save as default", tooltip="Save options as default options", change=lambda x: self.saveoptions(OPTIONFILE)))

		actionmenu = self.menuBar().addMenu(f"Actions")
		actionmenu.addAction(QQ(QAction, "mpltoolbar", parent=self, text="&Show MPL Toolbar", tooltip="Show or hide matplotlib toolbar", checkable=True))
		actionmenu.addSeparator()
		actionmenu.addAction(QQ(QAction, parent=self, text="&Rescale Plot", tooltip="Rescale plot when updating", change=lambda x: self.update_data(rescale=True)))
		actionmenu.addSeparator()
		actionmenu.addAction(QQ(QAction, parent=self, text="&Save Figure", tooltip="Save the figure", change=lambda x: self.savefigure()))
		actionmenu.addSeparator()
		actionmenu.addAction(QQ(QAction, parent=self, text="&Set Highpass Order", change=lambda _: self.change_highpass_order()))
		actionmenu.addSeparator()
		actionmenu.addAction(QQ(QAction, parent=self, text="&Apply to all", change=lambda _: self.apply_to_all()))

	def gui(self):
		self.gui_menu()
	
		layout = QVBoxLayout()

		self.fig = matplotlib.figure.Figure()
		axes = self.axes = self.fig.subplots(5, 1, gridspec_kw={'height_ratios': [0.5, 1, 0.5, 1, 1], 'hspace': 0, 'wspace': 0})
		axes[3].sharex(axes[4])
		axes[0].sharex(axes[1])


		self.plotcanvas = FigureCanvas(self.fig)
		self.plotcanvas.setMinimumHeight(200)
		self.plotcanvas.setMinimumWidth(200)
		layout.addWidget(self.plotcanvas, 2)
		
		ax = axes[0]
		self.cut_off_slider = matplotlib.widgets.Slider(ax, "Cut-Off", 0, 1, valinit=config['cutoff_freq'])
		self.cut_off_slider.on_changed(lambda x: config.__setitem__('cutoff_freq', x))

		ax = axes[1]
		self.fft_plot = ax.plot([], [], color="green", label="FFT Coefficients")[0]
		self.fft_cutoff_line = ax.axvline(x=config['cutoff_freq'], color="red", ls="--")
		ax.legend(loc="upper right")

		ax = axes[2]
		ax.axis("off")

		ax = axes[3]
		self.orig_plot = ax.plot([], [], color="#6ebeff", label="Original Spectrum")[0]
		self.base_plot = ax.plot([], [], color="#FF0266", label="Baseline", linewidth=3, alpha=0.3)[0]
		ax.get_xaxis().set_visible(False)
		ax.legend(loc="upper right")

		ax = axes[4]
		self.corr_plot = ax.plot([], [], color="#0336FF", label="Corrected Spectrum")[0]
		ax.legend(loc="upper right")

		self.config.register(['cutoff_freq', 'highpass'], self.update_data) 
		self.redrawplot.connect(self.fig.canvas.draw_idle)

		cid_1 = self.fig.canvas.mpl_connect('button_press_event', self.onclick) # Is now done by span selectors
		
		self.span_selectors = {}
		
		for i, ax in enumerate( (axes[1], axes[3], axes[4]) ):
			args = (lambda vmax, vmin, ax=ax: self.onzoom(vmax, vmin, ax), 'horizontal')
			kwargs = {'useblit': True}
			if ax == axes[1]:
				kwargs['button'] = 3
			self.span_selectors[i] = matplotlib.widgets.SpanSelector(ax, *args, **kwargs)


		self.mpltoolbar = NavigationToolbar2QT(self.plotcanvas, self)
		self.mpltoolbar.setVisible(self.config["mpltoolbar"])
		self.config.register("mpltoolbar", lambda: self.mpltoolbar.setVisible(self.config["mpltoolbar"]))
		self.addToolBar(self.mpltoolbar)

		self.notificationarea = QLabel()
		self.notificationarea.setWordWrap(True)
		self.notificationarea.setHidden(True)
		layout.addWidget(self.notificationarea)

		button_layout = QGridLayout()
		
		row_index = 0
		column_index = 0
		
		prev_button = QQ(QPushButton, text='Previous', change=lambda: self.update_selected_file(self.fileindex-1), shortcut='a')
		next_button = QQ(QPushButton, text='Next', change=lambda: self.update_selected_file(self.fileindex+1), shortcut='d')
		save_button = QQ(QPushButton, text='Save', change=lambda: self.save_file(), shortcut='s')


		button_layout.addWidget(prev_button, row_index, column_index)
		column_index += 1
		button_layout.addWidget(save_button, row_index, column_index)
		column_index += 1
		button_layout.addWidget(next_button, row_index, column_index)
		
		layout.addLayout(button_layout)
		widget = QWidget()
		self.setCentralWidget(widget)
		widget.setLayout(layout)


	def change_highpass_order(self):
		number, ok = QInputDialog.getInt(self, 'Highpass Order', 'Choose high pass order (0 for none): ')
		if not ok:
			return
		print(number)
		self.config['highpass'] = number

	def onclick(self, event):
		if event.inaxes == self.axes[1]:
			if event.button == 1:
				if isinstance(event.xdata,np.float64):
					self.cut_off_slider.set_val(event.xdata)
	
	def onzoom(self, vmin, vmax, ax):
		if vmin == vmax:
			return
		ax.set_xlim(vmin, vmax)
		self.update_data(rescale=False)

	def open_files(self, fnames=None):
		if not fnames:
			fnames, _ = QFileDialog.getOpenFileNames(None, 'Choose Files to open',"")
		if not fnames:
			self.notification("No files were selected. Keeping current data.")
			return
		
		self.files = fnames
		self.update_selected_file()

		
	def save_file(self):
		fname = self.files[self.fileindex]
		if fname is None:
			self.notification("No file selected.")
			return
		
		if self.config['asksavename']:
			savename, _ = QFileDialog.getSaveFileName(None, 'Choose File to Save to',"")
		else:
			basename, _ = os.path.splitext(fname)
			savename = basename + '.datfft'
		
		if not savename:
			self.notification("No filename specified for saving.")
			return

		# @Luis: Directly take corrected xs here
		xs, ys = self.data
		ys_corr = self.ys_corr

		data = np.vstack((xs, ys_corr)).T
		
		np.savetxt(savename, data, **self.config["savefile_kwargs"])
		self.notification(f"Saved data successfully to '{savename}'")

	def notification(self, text):
		self.notificationarea.setText(text)
		self.notificationarea.setHidden(False)

		if self.timer:
			self.timer.stop()
		self.timer = QTimer(self)
		self.timer.setSingleShot(True)
		self.timer.timeout.connect(lambda: self.notificationarea.setHidden(True))
		self.timer.start(5000)

	def saveoptions(self, filename=None):
		if filename is None:
			filename, _ = QFileDialog.getSaveFileName(self, "Save options to file")
			if not filename:
				return

		with open(filename, "w+") as optionfile:
			json.dump(self.config, optionfile, indent=2)
		self.notification("Options have been saved")

	def readoptions(self, filename=None, ignore=False):
		if filename is None:
			filename, _ = QFileDialog.getOpenFileName(self, "Read options from file")
			if not filename:
				return

		if not os.path.isfile(filename):
			if not ignore:
				self.notification(f"Option file '{filename}' does not exist.")
			return

		with open(filename, "r") as optionfile:
			values = json.load(optionfile)
		for key, value in values.items():
			self.config[key] = value
		self.notification("Options have been loaded")


	def savefigure(self):
		fname, _ = QFileDialog.getSaveFileName(None, 'Choose File to Save to',"")
		if not fname:
			return
		
		self.fig.savefig(fname, **config["savefigure_kwargs"])

	def update_selected_file(self, index=0):
		if not self.files:
			self.notification(f"No files are loaded.")
			return
		
		index = max(0, index)
		index = min(len(self.files)-1, index)
		self.fileindex = index
		fname = self.files[self.fileindex]
		
		data = np.genfromtxt(fname, delimiter="\t")
		xs = data[:, 0]
		ys = data[:, 1]

		self.data = xs, ys
		
		self.update_data(rescale=True)
		self.notification(f"File {index+1} out of {len(self.files)} currently selected. Name is {fname}.")


	def update_data(self, rescale=None):
		thread = threading.Thread(target=self.update_data_core, args=(rescale, ))
		with self.update_data_lock:
			thread.start()
			self.update_data_thread = thread.ident
		return(thread)

	def update_data_core(self, rescale):
		with self.update_data_lock:
			ownid = threading.current_thread().ident
		
		try:
			if self.data is None:
				return
			breakpoint(ownid, self.update_data_thread)
			
			xs, ys = self.data

			cutoff_freq = config['cutoff_freq']
			highpass = config['highpass']
			N = len(xs)
			
			fft_ys = scipy.fftpack.rfft(ys)
			fft_xs = scipy.fftpack.rfftfreq(N, xs[1]-xs[0])
			
			if highpass:
				filter_ys = high_pass_filter(fft_xs, cutoff_freq, highpass)
				fft_cut = fft_ys * filter_ys
				fft_bas = fft_ys * (1-filter_ys)
			else:
				filter_ys = fft_xs > cutoff_freq
				fft_cut = np.where(filter_ys, fft_ys, 0)
				fft_bas = np.where(~filter_ys, fft_ys, 0)
			
			ys_corr = scipy.fftpack.irfft(fft_cut)
			ys_base = scipy.fftpack.irfft(fft_bas)
			
			self.fft_plot.set_data(fft_xs, fft_ys)
			self.orig_plot.set_data(xs, ys)
			self.base_plot.set_data(xs, ys_base)
			self.corr_plot.set_data(xs, ys_corr)
			self.fft_cutoff_line.set_xdata([cutoff_freq])

			self.ys_corr = ys_corr
			
			breakpoint(ownid, self.update_data_thread)
			
			if rescale:
				margin = self.config['margin']
				axes = self.axes
				x_range = (np.nanmin(xs), np.nanmax(xs))
				mask = (x_range[0] < xs) & (x_range[1] > xs)
				y_range = calculate_y_limits(ys[mask], margin)
				y_range_corr = calculate_y_limits(ys_corr[mask], margin)
				y_range = (min(y_range[0], y_range_corr[0]), max(y_range[1], y_range_corr[1]))
				y_range_fft = calculate_y_limits(fft_ys, margin)

				for ax in (axes[3], axes[4]):
					ax.set_xlim(x_range)
					ax.set_ylim(y_range)
				
				axes[4].set_xticks(np.linspace(*x_range, 5))
				axes[4].set_xticklabels([f"{x:.2f}" for x in np.linspace(*x_range, 5)])

				fft_range = (np.nanmin(fft_xs), np.nanmax(fft_xs))
				fft_padding = (fft_range[1] - fft_range[0]) * 0.05
				fft_range = (fft_range[0] - fft_padding, fft_range[1] + fft_padding)

				self.cut_off_slider.valmin = fft_range[0]
				self.cut_off_slider.valmax = fft_range[1]
				axes[0].set_xlim(fft_range)

				axes[1].set_xlim(fft_range)
				axes[1].set_ylim(y_range_fft)
			
			self.redrawplot.emit()
		except BreakpointError as E:
			pass

	def apply_to_all(self):
		cutoff_freq = config['cutoff_freq']
		highpass = config['highpass']
		
		for fname in self.files:
			data = np.genfromtxt(fname, delimiter="\t")
			xs = data[:, 0]
			ys = data[:, 1]
			
			N = len(xs)
			
			fft_ys = scipy.fftpack.rfft(ys)
			fft_xs = scipy.fftpack.rfftfreq(N, xs[1]-xs[0])
			
			if highpass:
				filter_ys = high_pass_filter(fft_xs, cutoff_freq, highpass)
				fft_cut = fft_ys * filter_ys
				fft_bas = fft_ys * (1-filter_ys)
			else:
				filter_ys = fft_xs > cutoff_freq
				fft_cut = np.where(filter_ys, fft_ys, 0)
				fft_bas = np.where(~filter_ys, fft_ys, 0)
			
			ys_corr = scipy.fftpack.irfft(fft_cut)
			ys_base = scipy.fftpack.irfft(fft_bas)
			
			###
			basename, _ = os.path.splitext(fname)
			savename = basename + '.datfft'

			# @Luis: Directly take corrected xs here
			data = np.vstack((xs, ys_corr)).T
			
			np.savetxt(savename, data, **self.config["savefile_kwargs"])
		
		self.notification(f"Saved data successfully for {len(self.files)} files.")

class Config(dict):
	def __init__(self, signal, init_values={}):
		super().__init__(init_values)
		self.signal = signal
		self.signal.connect(self.callback)
		self.callbacks = pd.DataFrame(columns=["id", "key", "widget", "function"], dtype="object").astype({"id": np.uint})

	def __setitem__(self, key, value, widget=None):
		super().__setitem__(key, value)
		self.signal.emit((key, value, widget))

	def callback(self, args):
		key, value, widget = args
		if widget:
			callbacks_widget = self.callbacks.query(f"key == @key and widget != @widget")
		else:
			callbacks_widget = self.callbacks.query(f"key == @key")
		for i, row in callbacks_widget.iterrows():
			row["function"]()

	def register(self, keys, function):
		if not isinstance(keys, (tuple, list)):
			keys = [keys]
		for key in keys:
			id = 0
			df = self.callbacks
			df.loc[len(df), ["id", "key", "function"]] = id, key, function

	def register_widget(self, key, widget, function):
		ids = set(self.callbacks["id"])
		id = 1
		while id in ids:
			id += 1
		df = self.callbacks
		df.loc[len(df), ["id", "key", "function", "widget"]] = id, key, function, widget
		widget.destroyed.connect(lambda x, id=id: self.unregister_widget(id))

	def unregister_widget(self, id):
		self.callbacks.drop(self.callbacks[self.callbacks["id"] == id].index, inplace=True)

def QQ(widgetclass, config_key=None, **kwargs):
	widget = widgetclass()

	if "range" in kwargs:
		widget.setRange(*kwargs["range"])
	if "maxWidth" in kwargs:
		widget.setMaximumWidth(kwargs["maxWidth"])
	if "maxHeight" in kwargs:
		widget.setMaximumHeight(kwargs["maxHeight"])
	if "minWidth" in kwargs:
		widget.setMinimumWidth(kwargs["minWidth"])
	if "minHeight" in kwargs:
		widget.setMinimumHeight(kwargs["minHeight"])
	if "color" in kwargs:
		widget.setColor(kwargs["color"])
	if "text" in kwargs:
		widget.setText(kwargs["text"])
	if "options" in kwargs:
		options = kwargs["options"]
		if isinstance(options, dict):
			for key, value in options.items():
				widget.addItem(key, value)
		else:
			for option in kwargs["options"]:
				widget.addItem(option)
	if "width" in kwargs:
		widget.setFixedWidth(kwargs["width"])
	if "tooltip" in kwargs:
		widget.setToolTip(kwargs["tooltip"])
	if "placeholder" in kwargs:
		widget.setPlaceholderText(kwargs["placeholder"])
	if "singlestep" in kwargs:
		widget.setSingleStep(kwargs["singlestep"])
	if "wordwrap" in kwargs:
		widget.setWordWrap(kwargs["wordwrap"])
	if "align" in kwargs:
		widget.setAlignment(kwargs["align"])
	if "rowCount" in kwargs:
		widget.setRowCount(kwargs["rowCount"])
	if "columnCount" in kwargs:
		widget.setColumnCount(kwargs["columnCount"])
	if "move" in kwargs:
		widget.move(*kwargs["move"])
	if "default" in kwargs:
		widget.setDefault(kwargs["default"])
	if "textFormat" in kwargs:
		widget.setTextFormat(kwargs["textFormat"])
	if "checkable" in kwargs:
		widget.setCheckable(kwargs["checkable"])
	if "shortcut" in kwargs:
		widget.setShortcut(kwargs["shortcut"])
	if "parent" in kwargs:
		widget.setParent(kwargs["parent"])
	if "completer" in kwargs:
		widget.setCompleter(kwargs["completer"])
	if "hidden" in kwargs:
		widget.setHidden(kwargs["hidden"])
	if "visible" in kwargs:
		widget.setVisible(kwargs["visible"])
	if "stylesheet" in kwargs:
		widget.setStyleSheet(kwargs["stylesheet"])
	if "enabled" in kwargs:
		widget.setEnabled(kwargs["enabled"])
	if "items" in kwargs:
		for item in kwargs["items"]:
			widget.addItem(item)
	if "readonly" in kwargs:
		widget.setReadOnly(kwargs["readonly"])
	if "prefix" in kwargs:
		widget.setPrefix(kwargs["prefix"])

	if widgetclass in [QSpinBox, QDoubleSpinBox]:
		setter = widget.setValue
		changer = widget.valueChanged.connect
		getter = widget.value
	elif widgetclass == QCheckBox:
		setter = widget.setChecked
		changer = widget.stateChanged.connect
		getter = widget.isChecked
	elif widgetclass == QPlainTextEdit:
		setter = widget.setPlainText
		changer = widget.textChanged.connect
		getter = widget.toPlainText
	elif widgetclass == QLineEdit:
		setter = widget.setText
		changer = widget.textChanged.connect
		getter = widget.text
	elif widgetclass == QAction:
		setter = widget.setChecked
		changer = widget.triggered.connect
		getter = widget.isChecked
	elif widgetclass == QPushButton:
		setter = widget.setDefault
		changer = widget.clicked.connect
		getter = widget.isDefault
	elif widgetclass == QToolButton:
		setter = widget.setChecked
		changer = widget.clicked.connect
		getter = widget.isChecked
	elif widgetclass == QComboBox:
		setter = widget.setCurrentText
		changer = widget.currentTextChanged.connect
		getter = widget.currentText
	else:
		return widget

	if "value" in kwargs:
		setter(kwargs["value"])
	if config_key:
		setter(config[config_key])
		changer(lambda x=None, key=config_key: config.__setitem__(key, getter(), widget))
		config.register_widget(config_key, widget, lambda: setter(config[config_key]))
	if "change" in kwargs:
		changer(kwargs["change"])
	if "changes" in kwargs:
		for change in kwargs["changes"]:
			changer(change)

	return widget

class BreakpointError(Exception):
	pass

def breakpoint(ownid, lastid):
	if ownid != lastid:
		raise BreakpointError()

def except_hook(cls, exception, traceback):
	sys.__excepthook__(cls, exception, traceback)
	window.notification(f"{exception}\n{''.join(tb.format_tb(traceback))}")


def start_gui(kwargs):
	sys.excepthook = except_hook
	app = QApplication(sys.argv)
	window = MainWindow(**kwargs)
	sys.exit(app.exec())


def start():
	epilog = 'Program to fourier filter periodic baselines from measurements.'
	parser = argparse.ArgumentParser(prog='FFT-Filter', epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('files', nargs='*', type=str, help='Glob string for files to be loaded')
	args = parser.parse_args()
	
	kwargs = {}
	
	if args.files:
		files = [ file for glob_str in args.files for file in glob.glob(glob_str, recursive=True) ]
		kwargs['files'] = files
	else:
		kwargs['files'] = []

	start_gui(kwargs)

if __name__ == '__main__':
	start()