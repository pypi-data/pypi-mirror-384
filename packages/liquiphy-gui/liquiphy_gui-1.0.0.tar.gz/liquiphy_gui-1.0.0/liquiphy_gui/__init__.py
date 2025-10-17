#  liquiphy_gui/__init__.py
#
#  Copyright 2025 Leon Dionne <ldionne@dridesign.sh.cn>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
"""
A simple graphical front-end to liquidsfz.

To install file associatons, run the "liquiphy-gui-install" in a terminal.
Afterwards, you can click on an SFZ file in your file explorer (nemo, nautilus,
etc.), and get an instant preview of the selected SFZ.
"""
import sys, logging, argparse
from os.path import dirname, basename, abspath
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import	QApplication, QDialog, QLabel, QFrame, QTabWidget, QTextEdit, \
							QVBoxLayout, QHBoxLayout
from conn_jack import JackConnectionManager, JackConnectError, JACK_PORT_IS_INPUT
from qt_extras.list_button import QtListButton
from liquiphy import LiquidSFZ

__version__ = "1.0.0"


class Dialog(QDialog):

	sig_ports_ready = pyqtSignal()

	def __init__(self, sfz_filename):
		super().__init__()

		tabs = QTabWidget(self)
		error_text = QTextEdit(tabs)
		error_text.setReadOnly(True)

		try:
			self.conn_man = JackConnectionManager()
		except JackConnectError:
			error_text.insertPlainText('Could not connect to JACK server. Is it running?')
		else:
			sfz_frame = QFrame(tabs)
			sfz_layout = QVBoxLayout(sfz_frame)
			self.settings = QSettings('ZenSoSo', 'liquiphy_gui')
			self.midi_in_port = None
			self.audio_out_ports = []
			self.current_midi_source_port = None
			self.current_audio_sink_ports = []
			self.sig_ports_ready.connect(self.slot_ports_ready, type = Qt.QueuedConnection)
			self.conn_man.on_client_registration(self.on_client_registration)
			self.conn_man.on_port_registration(self.on_port_registration)
			self.liquidsfz = LiquidSFZ(sfz_filename)
			error_text.insertPlainText(self.liquidsfz.stderr())

			# Show selected SFZ:
			label = QLabel(basename(sfz_filename), self)
			font = label.font()
			font.setPointSize(15)
			label.setFont(font)
			label.setAlignment(Qt.AlignHCenter| Qt.AlignVCenter)
			sfz_layout.addWidget(label)
			label = QLabel(dirname(abspath(sfz_filename)), self)
			label.setAlignment(Qt.AlignHCenter| Qt.AlignVCenter)
			sfz_layout.addWidget(label)

			lo = QHBoxLayout()

			# Setup input select button:
			label = QLabel('Source:', self)
			label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
			lo.addWidget(label)
			self.b_input = QtListButton(self, self.midi_sources)
			self.b_input.sig_item_selected.connect(self.slot_input_selected)
			self.b_input.setEnabled(False)
			lo.addWidget(self.b_input)

			# Setup output select button:
			label = QLabel('Sink:', self)
			label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
			lo.addWidget(label)
			self.b_output = QtListButton(self, self.audio_targets)
			self.b_output.sig_item_selected.connect(self.slot_output_client_selected)
			self.b_output.setEnabled(False)
			lo.addWidget(self.b_output)
			sfz_layout.addLayout(lo)

			tabs.addTab(sfz_frame, 'Main')

		tabs.addTab(error_text, 'Errors')
		main_layout = QVBoxLayout()
		main_layout.setContentsMargins(2,2,2,2)
		main_layout.addWidget(tabs)
		self.setLayout(main_layout)

	def midi_sources(self):
		"""
		Returns a list of MIDI out port which the previewer can connect to.
		This provides the text and data for the QtListButton "b_input".
		"""
		return list((port.name, port) for port in self.conn_man.output_ports() if port.is_midi)

	def audio_targets(self):
		"""
		Returns a list of audio in clients which the previewer can connect to.
		This provides the text and data for the QtListButton "b_output".
		"""
		return list((client, client) for client in self.conn_man.physical_playback_clients())

	@property
	def selected_midi_source(self):
		return self.settings.value('MIDI-Source', '')

	@selected_midi_source.setter
	def selected_midi_source(self, value):
		self.settings.setValue('MIDI-Source', value)

	@property
	def selected_audio_sink(self):
		return self.settings.value('Audio-Sink', '')

	@selected_audio_sink.setter
	def selected_audio_sink(self, value):
		self.settings.setValue('Audio-Sink', value)

	@pyqtSlot(str)
	def slot_input_selected(self, value):
		logging.debug('slot_input_selected')
		if self.current_midi_source_port:
			self.conn_man.disconnect_by_name(self.current_midi_source_port, self.midi_in_port.name)
		self.selected_midi_source = value
		if value:
			self.connect_midi_source(value)
		else:
			self.current_midi_source_port = None

	@pyqtSlot(str)
	def slot_output_client_selected(self, value):
		if self.current_audio_sink_ports:
			for src,tgt in zip(self.audio_out_ports, self.current_audio_sink_ports):
				self.conn_man.disconnect(src, tgt)
		self.selected_audio_sink = value
		if value:
			self.connect_audio_sinks(value)
		else:
			self.current_audio_sink_ports = []

	def connect_midi_source(self, port_name):
		self.conn_man.connect_by_name(port_name, self.midi_in_port.name)
		self.current_midi_source_port = port_name

	def connect_audio_sinks(self, client_name):
		self.current_audio_sink_ports = [ port for port \
			in self.conn_man.get_client_ports(client_name) \
			if port.is_input ]
		for src,tgt in zip(self.audio_out_ports, self.current_audio_sink_ports):
			self.conn_man.connect(src, tgt)

	def on_client_registration(self, client_name, action):
		if client_name.startswith('liquidsfz'):
			self.liq_name = client_name

	def on_port_registration(self, port, action):
		if port.name.startswith(self.liq_name + ':'):
			if port.is_input and port.is_midi:
				self.midi_in_port = port
			elif port.is_output and port.is_audio:
				self.audio_out_ports.append(port)
		if self.midi_in_port and len(self.audio_out_ports) == 2:
			self.sig_ports_ready.emit()

	@pyqtSlot()
	def slot_ports_ready(self):
		if self.selected_midi_source:
			self.b_input.select_text(self.selected_midi_source)
		if self.selected_audio_sink:
			self.b_output.select_text(self.selected_audio_sink)
		self.b_input.setEnabled(True)
		self.b_output.setEnabled(True)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('Filename', type = str, help = 'SFZ file to preview.')
	parser.add_argument("--verbose", "-v", action="store_true",
		help = "Show more detailed debug information")
	parser.epilog = __doc__
	options = parser.parse_args()
	log_level = logging.DEBUG if options.verbose else logging.ERROR
	log_format = "[%(filename)24s:%(lineno)4d] %(levelname)-8s %(message)s"
	logging.basicConfig(level = log_level, format = log_format)
	app = QApplication([])
	dialog = Dialog(options.Filename)
	dialog.exec()



if __name__ == "__main__":
	main()



#  end liquiphy_gui/__init__.py
