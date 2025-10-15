#  simple_carla/scripts/sc_plugin_info.py
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
Allows the user to select a plugin using Carla's plugin dialog and display a
bunch of info about the plugin in a human -readable format.
"""
import argparse, logging
from threading import Event
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, pyqtSlot
from simple_carla.qt import CarlaQt, QtPlugin, Plugin
from simple_carla.plugin_dialog import CarlaPluginDialog


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()
		self.ready_event = Event()
		self.carla = CarlaQt('carla')
		self.carla.sig_engine_started.connect(self.slot_engine_started)
		if not self.carla.engine_init():
			audio_error = self.carla.get_last_error()
			if audio_error:
				raise RuntimeError(f'Could not start carla; possible reasons:\n{audio_error}')
			raise RuntimeError('Could not start carla')

	@pyqtSlot(int, int, int, int, float, str)
	def slot_engine_started(self, *_):
		logging.debug('======= Engine started ======== ')
		self.ready_event.set()

	def show_dialog(self):
		self.ready_event.wait()
		plugin_def = CarlaPluginDialog(self).exec_dialog()
		if plugin_def is None:
			self.close()
		else:
			plugin = QtPlugin(plugin_def)
			plugin.sig_ready.connect(self.plugin_ready, type = Qt.QueuedConnection)
			plugin.add_to_carla()

	@pyqtSlot(Plugin)
	def plugin_ready(self, plugin):
		logging.debug('Received sig_ready from %s', plugin)
		print(f"""
Plugin Name:          {plugin.original_plugin_name}
Audio Inputs:         {plugin.audio_in_count}
Audio Outputs:        {plugin.audio_out_count}
MIDI Inputs:          {plugin.midi_in_count}
MIDI Outputs:         {plugin.midi_out_count}
Input Parameters:     {plugin.input_parameter_count}
Output Parameters:    {plugin.output_parameter_count}
Maker:                {plugin.maker}
Category:             {plugin.category}
Label:                {plugin.label}
Filename:             {plugin.filename}
""")
		for param in plugin.parameters.values():
			param.type_name = 'Boolean' if param.is_boolean \
				else 'Integer' if param.is_integer \
				else 'Float'
			for label, att in [
				('Parameter:           ', 'name'),
				('Symbol:              ', 'symbol'),
				('Comment:             ', 'comment'),
				('Group Name:          ', 'groupName'),
				('Unit:                ', 'unit'),
				('Enabled:             ', 'is_enabled'),
				('Type:                ', 'type_name'),
				('Min:                 ', 'min'),
				('Max:                 ', 'max'),
				('Step:                ', 'step'),
				('Automatable:         ', 'is_automatable'),
				('Read only:           ', 'is_read_only'),
				('Uses samplerate:     ', 'uses_samplerate'),
				('Uses scalepoints:    ', 'uses_scalepoints'),
				('Scale point count:   ', 'scalePointCount'),
				('Uses custom text:    ', 'uses_custom_text'),
				('Can be CV controlled:', 'can_be_cv_controlled')
			]:
				try:
					print(label, getattr(param, att));
				except AttributeError:
					pass
			print()
		self.carla.delete()
		QApplication.instance().quit()


def main():
	p = argparse.ArgumentParser()
	p.epilog = __doc__
	p.add_argument("--verbose", "-v", action = "store_true",
		help = "Show detailed debug information")
	options = p.parse_args()
	logging.basicConfig(
		level = logging.DEBUG if options.verbose else logging.ERROR,
		format = "[%(filename)24s:%(lineno)-4d] %(levelname)-8s %(message)s"
	)
	app = QApplication([])
	window = MainWindow()
	window.show_dialog()
	app.exec()


if __name__ == "__main__":
	main()


#  end simple_carla/scripts/sc_plugin_info.py
