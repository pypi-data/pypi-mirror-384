from PyQt5.QtWidgets import QMessageBox, QComboBox, QFrame, QCheckBox, QFileDialog, QGridLayout, QLineEdit, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QSize
from celldetective.gui.layouts import ChannelNormGenerator
from superqt import QLabeledDoubleSlider, QLabeledSlider, QSearchableComboBox
from superqt.fonticon import icon
from fonticon_mdi6 import MDI6
from celldetective.io import locate_signal_dataset, get_signal_datasets_list, load_experiment_tables
from celldetective.signals import train_signal_model
import numpy as np
import json
import os
from glob import glob
from datetime import datetime
from pandas.api.types import is_numeric_dtype
from celldetective.gui.processes.train_signal_model import TrainSignalModelProcess
from celldetective.gui.workers import ProgressWindow
from celldetective.gui.settings._settings_base import CelldetectiveSettingsPanel

class SettingsEventDetectionModelTraining(CelldetectiveSettingsPanel):
	
	"""
	UI to set measurement instructions.

	"""

	def __init__(self, parent_window=None, signal_mode='single-cells'):
		
		self.parent_window = parent_window
		self.mode = self.parent_window.mode
		self.exp_dir = self.parent_window.exp_dir
		self.pretrained_model = None
		self.dataset_folder = None
		self.current_neighborhood = None
		self.reference_population = None
		self.neighbor_population = None
		self.signal_mode = signal_mode
		
		super().__init__(title="Train event detection model")

		if self.signal_mode=='single-cells':
			self.signal_models_dir = self._software_path+os.sep+os.sep.join(['celldetective','models','signal_detection'])
		elif self.signal_mode=='pairs':
			self.signal_models_dir = self._software_path+os.sep+os.sep.join(['celldetective','models','pair_signal_detection'])
			self.mode = 'pairs'
		
		self._add_to_layout()
		self._load_previous_instructions()
		
		self._adjustSize()
		new_width = int(self.width()*1.2)
		self.resize(new_width, int(self._screen_height * 0.8))
		self.setMinimumWidth(new_width)
	
	def _add_to_layout(self):
		self._layout.addWidget(self.model_frame)
		self._layout.addWidget(self.data_frame)
		self._layout.addWidget(self.hyper_frame)
		self._layout.addWidget(self.submit_btn)

	def _create_widgets(self):

		"""
		Create the multibox design.

		"""
		super()._create_widgets()
		
		# first frame for FEATURES
		self.model_frame = QFrame()
		self.model_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
		self.populate_model_frame()

		self.data_frame = QFrame()
		self.data_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
		self.populate_data_frame()

		self.hyper_frame = QFrame()
		self.hyper_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
		self.populate_hyper_frame()

		self.submit_btn.setEnabled(False)
		self.submit_btn.setText("Train")


	def populate_hyper_frame(self):

		"""
		Add widgets and layout in the POST-PROCESSING frame.
		"""

		grid = QGridLayout(self.hyper_frame)
		grid.setContentsMargins(30,30,30,30)
		grid.setSpacing(30)

		self.hyper_lbl = QLabel("HYPERPARAMETERS")
		self.hyper_lbl.setStyleSheet("""
			font-weight: bold;
			padding: 0px;
			""")
		grid.addWidget(self.hyper_lbl, 0, 0, 1, 4, alignment=Qt.AlignCenter)
		self.generate_hyper_contents()
		grid.addWidget(self.ContentsHyper, 1, 0, 1, 4, alignment=Qt.AlignTop)

	def generate_hyper_contents(self):

		self.ContentsHyper = QFrame()
		layout = QVBoxLayout(self.ContentsHyper)
		layout.setContentsMargins(0,0,0,0)

		lr_layout = QHBoxLayout()
		lr_layout.addWidget(QLabel('learning rate: '),30)
		self.lr_le = QLineEdit('0,01')
		self.lr_le.setValidator(self._floatValidator)
		lr_layout.addWidget(self.lr_le, 70)
		layout.addLayout(lr_layout)

		bs_layout = QHBoxLayout()
		bs_layout.addWidget(QLabel('batch size: '),30)
		self.bs_le = QLineEdit('64')
		self.bs_le.setValidator(self._intValidator)
		bs_layout.addWidget(self.bs_le, 70)
		layout.addLayout(bs_layout)

		epochs_layout = QHBoxLayout()
		epochs_layout.addWidget(QLabel('# epochs: '), 30)
		self.epochs_slider = QLabeledSlider()
		self.epochs_slider.setRange(1,3000)
		self.epochs_slider.setSingleStep(1)
		self.epochs_slider.setTickInterval(1)		
		self.epochs_slider.setOrientation(Qt.Horizontal)
		self.epochs_slider.setValue(300)
		epochs_layout.addWidget(self.epochs_slider, 70)
		layout.addLayout(epochs_layout)


	def populate_data_frame(self):

		"""
		Add widgets and layout in the POST-PROCESSING frame.
		"""

		grid = QGridLayout(self.data_frame)
		grid.setContentsMargins(30,30,30,30)
		grid.setSpacing(30)

		self.data_lbl = QLabel("DATA")
		self.data_lbl.setStyleSheet("""
			font-weight: bold;
			padding: 0px;
			""")
		grid.addWidget(self.data_lbl, 0, 0, 1, 4, alignment=Qt.AlignCenter)
		self.generate_data_contents()
		grid.addWidget(self.ContentsData, 1, 0, 1, 4, alignment=Qt.AlignTop)

	def populate_model_frame(self):

		"""
		Add widgets and layout in the FEATURES frame.
		"""

		grid = QGridLayout(self.model_frame)
		grid.setContentsMargins(30,30,30,30)
		grid.setSpacing(30)

		self.model_lbl = QLabel("MODEL")
		self.model_lbl.setStyleSheet("""
			font-weight: bold;
			padding: 0px;
			""")
		grid.addWidget(self.model_lbl, 0, 0, 1, 4, alignment=Qt.AlignCenter)

		self.generate_model_panel_contents()
		grid.addWidget(self.ContentsModel, 1, 0, 1, 4, alignment=Qt.AlignTop)


	def generate_data_contents(self):

		self.ContentsData = QFrame()
		layout = QVBoxLayout(self.ContentsData)
		layout.setContentsMargins(0,0,0,0)

		train_data_layout = QHBoxLayout()
		train_data_layout.addWidget(QLabel('Training data: '), 30)
		self.select_data_folder_btn = QPushButton('Choose folder')
		self.select_data_folder_btn.clicked.connect(self.showDialog_dataset)
		self.data_folder_label = QLabel('No folder chosen')
		train_data_layout.addWidget(self.select_data_folder_btn, 35)
		train_data_layout.addWidget(self.data_folder_label, 30)

		self.cancel_dataset = QPushButton()
		self.cancel_dataset.setIcon(icon(MDI6.close,color="black"))
		self.cancel_dataset.clicked.connect(self.clear_dataset)
		self.cancel_dataset.setStyleSheet(self.button_select_all)
		self.cancel_dataset.setIconSize(QSize(20, 20))
		self.cancel_dataset.setVisible(False)
		train_data_layout.addWidget(self.cancel_dataset, 5)


		layout.addLayout(train_data_layout)

		include_dataset_layout = QHBoxLayout()
		include_dataset_layout.addWidget(QLabel('include dataset: '),30)
		self.dataset_cb = QComboBox()

		available_datasets, self.datasets_path = get_signal_datasets_list(return_path=True)
		signal_datasets = ['--'] + available_datasets

		self.dataset_cb.addItems(signal_datasets)
		include_dataset_layout.addWidget(self.dataset_cb, 70)
		layout.addLayout(include_dataset_layout)

		augmentation_hbox = QHBoxLayout()
		augmentation_hbox.addWidget(QLabel('augmentation\nfactor: '), 30)
		self.augmentation_slider = QLabeledDoubleSlider()
		self.augmentation_slider.setSingleStep(0.01)
		self.augmentation_slider.setTickInterval(0.01)		
		self.augmentation_slider.setOrientation(Qt.Horizontal)
		self.augmentation_slider.setRange(1, 5)
		self.augmentation_slider.setValue(2)

		augmentation_hbox.addWidget(self.augmentation_slider, 70)
		layout.addLayout(augmentation_hbox)

		validation_split_layout = QHBoxLayout()
		validation_split_layout.addWidget(QLabel('validation split: '),30)
		self.validation_slider = QLabeledDoubleSlider()
		self.validation_slider.setSingleStep(0.01)
		self.validation_slider.setTickInterval(0.01)		
		self.validation_slider.setOrientation(Qt.Horizontal)
		self.validation_slider.setRange(0,0.9)
		self.validation_slider.setValue(0.25)		
		validation_split_layout.addWidget(self.validation_slider, 70)
		layout.addLayout(validation_split_layout)


	def generate_model_panel_contents(self):
		
		self.ContentsModel = QFrame()
		layout = QVBoxLayout(self.ContentsModel)
		layout.setContentsMargins(0,0,0,0)

		modelname_layout = QHBoxLayout()
		modelname_layout.addWidget(QLabel('Model name: '), 30)
		self.modelname_le = QLineEdit()
		self.modelname_le.setText(f"Untitled_model_{datetime.today().strftime('%Y-%m-%d')}")
		modelname_layout.addWidget(self.modelname_le, 70)
		layout.addLayout(modelname_layout)

		if self.signal_mode=='pairs':
			neighborhood_layout = QHBoxLayout()
			neighborhood_layout.addWidget(QLabel('neighborhood of interest: '), 30)
			self.neighborhood_choice_cb = QSearchableComboBox()
			self.fill_available_neighborhoods()
			neighborhood_layout.addWidget(self.neighborhood_choice_cb, 70)
			layout.addLayout(neighborhood_layout)			

		classname_layout = QHBoxLayout()
		classname_layout.addWidget(QLabel('event name: '), 30)
		self.class_name_le = QLineEdit()
		self.class_name_le.setText("")
		classname_layout.addWidget(self.class_name_le, 70)
		layout.addLayout(classname_layout)

		pretrained_layout = QHBoxLayout()
		pretrained_layout.setContentsMargins(0,0,0,0)
		pretrained_layout.addWidget(QLabel('Pretrained model: '), 30)

		self.browse_pretrained_btn = QPushButton('Choose folder')
		self.browse_pretrained_btn.clicked.connect(self.showDialog_pretrained)
		pretrained_layout.addWidget(self.browse_pretrained_btn, 35)

		self.pretrained_lbl = QLabel('No folder chosen')
		pretrained_layout.addWidget(self.pretrained_lbl, 30)

		self.cancel_pretrained = QPushButton()
		self.cancel_pretrained.setIcon(icon(MDI6.close,color="black"))
		self.cancel_pretrained.clicked.connect(self.clear_pretrained)
		self.cancel_pretrained.setStyleSheet(self.button_select_all)
		self.cancel_pretrained.setIconSize(QSize(20, 20))
		self.cancel_pretrained.setVisible(False)
		pretrained_layout.addWidget(self.cancel_pretrained, 5)

		layout.addLayout(pretrained_layout)

		recompile_layout = QHBoxLayout()
		recompile_layout.addWidget(QLabel('Recompile: '), 30)
		self.recompile_option = QCheckBox()
		self.recompile_option.setEnabled(False)
		recompile_layout.addWidget(self.recompile_option, 70)
		layout.addLayout(recompile_layout)

		self.max_nbr_channels = 5
		self.ch_norm = ChannelNormGenerator(self, mode='signals')
		layout.addLayout(self.ch_norm)

		if self.signal_mode=='pairs':
			self.neighborhood_choice_cb.currentIndexChanged.connect(self.neighborhood_changed)
			self.neighborhood_changed()

		model_length_layout = QHBoxLayout()
		model_length_layout.addWidget(QLabel('Max signal length: '), 30)
		self.model_length_slider = QLabeledSlider()
		self.model_length_slider.setSingleStep(1)
		self.model_length_slider.setTickInterval(1)
		self.model_length_slider.setSingleStep(1)
		self.model_length_slider.setOrientation(Qt.Horizontal)
		self.model_length_slider.setRange(0,1024)
		self.model_length_slider.setValue(128)		
		model_length_layout.addWidget(self.model_length_slider, 70)
		layout.addLayout(model_length_layout)

	def neighborhood_changed(self):

		neigh = self.neighborhood_choice_cb.currentText()
		self.current_neighborhood = neigh
		for pop in self.dataframes.keys():
			self.current_neighborhood = self.current_neighborhood.replace(f'{pop}_ref_', '')

		self.reference_population = self.neighborhood_choice_cb.currentText().split('_')[0]
		if '_(' in self.current_neighborhood and ')_' in self.current_neighborhood:
			self.neighbor_population = self.current_neighborhood.split('_(')[-1].split(')_')[0].split('-')[-1]
			self.reference_population = self.current_neighborhood.split('_(')[-1].split(')_')[0].split('-')[0]
		else:
			if 'self' in self.current_neighborhood:
				self.neighbor_population = self.reference_population

		print(f'Current neighborhood: {self.current_neighborhood}')
		print(f'New reference population: {self.reference_population}')
		print(f'New neighbor population: {self.neighbor_population}')

		self.df_reference = self.dataframes[self.reference_population]
		self.df_neighbor = self.dataframes[self.neighbor_population]
		self.df_pairs = load_experiment_tables(self.parent_window.exp_dir, population='pairs', load_pickle=False)

		self.df_reference = self.df_reference.rename(columns=lambda x: 'reference_' + x)
		num_cols_reference = [c for c in list(self.df_reference.columns) if is_numeric_dtype(self.df_reference[c])]
		self.df_neighbor = self.df_neighbor.rename(columns=lambda x: 'neighbor_' + x)
		num_cols_neighbor = [c for c in list(self.df_neighbor.columns) if is_numeric_dtype(self.df_neighbor[c])]
		self.df_pairs = self.df_pairs.rename(columns=lambda x: 'pair_' + x)
		num_cols_pairs = [c for c in list(self.df_pairs.columns) if is_numeric_dtype(self.df_pairs[c])]

		self.signals = ['--'] + num_cols_pairs + num_cols_reference + num_cols_neighbor

		for cb in self.ch_norm.channel_cbs:
			cb.clear()
			cb.addItems(self.signals)

	def fill_available_neighborhoods(self):

		self.dataframes = {}
		self.neighborhood_cols = []
		for population in self.parent_window.parent_window.populations:
			df_pop = load_experiment_tables(self.parent_window.exp_dir, population=population, load_pickle=True)
			self.dataframes.update({population: df_pop})
			if df_pop is not None:
				self.neighborhood_cols.extend(
					[f'{population}_ref_' + c for c in list(df_pop.columns) if c.startswith('neighborhood')])

		self.neighborhood_choice_cb.addItems(self.neighborhood_cols)

	def showDialog_pretrained(self):

		self.pretrained_model = QFileDialog.getExistingDirectory(
						self, "Open Directory",
						os.sep.join([self.soft_path,'celldetective','models','signal_detection','']),
						QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
						)

		if self.pretrained_model is not None:
		# 	self.foldername = self.file_dialog_pretrained.selectedFiles()[0]
			subfiles = glob(os.sep.join([self.pretrained_model,"*"]))
			if os.sep.join([self.pretrained_model,"config_input.json"]) in subfiles:
				self.load_pretrained_config()
				self.pretrained_lbl.setText(self.pretrained_model.split(os.sep)[-1])
				self.cancel_pretrained.setVisible(True)
				self.recompile_option.setEnabled(True)
				self.modelname_le.setText(f"{self.pretrained_model.split(os.sep)[-1]}_{datetime.today().strftime('%Y-%m-%d')}")
			else:
				self.pretrained_model = None
				self.pretrained_lbl.setText('No folder chosen')	
				self.recompile_option.setEnabled(False)	
				self.cancel_pretrained.setVisible(False)
		print(self.pretrained_model)

	def showDialog_dataset(self):

		self.dataset_folder = QFileDialog.getExistingDirectory(
						self, "Open Directory",
						self.exp_dir,
						QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
						)
		if self.dataset_folder is not None:

			subfiles = glob(os.sep.join([self.dataset_folder,"*.npy"]))
			if len(subfiles)>0:
				print(f'found {len(subfiles)} files in folder')
				self.data_folder_label.setText(self.dataset_folder[:16]+'...')
				self.data_folder_label.setToolTip(self.dataset_folder)
				self.cancel_dataset.setVisible(True)
			else:
				self.data_folder_label.setText('No folder chosen')
				self.data_folder_label.setToolTip('')
				self.dataset_folder = None
				self.cancel_dataset.setVisible(False)

	def clear_pretrained(self):
		
		self.pretrained_model = None
		self.pretrained_lbl.setText('No folder chosen')
		for cb in self.ch_norm.channel_cbs:
			cb.setEnabled(True)
		self.ch_norm.add_col_btn.setEnabled(True)
		self.recompile_option.setEnabled(False)
		self.cancel_pretrained.setVisible(False)
		self.model_length_slider.setEnabled(True)
		self.class_name_le.setText('')
		self.modelname_le.setText(f"Untitled_model_{datetime.today().strftime('%Y-%m-%d')}")

	def clear_dataset(self):

		self.dataset_folder = None
		self.data_folder_label.setText('No folder chosen')
		self.data_folder_label.setToolTip('')
		self.cancel_dataset.setVisible(False)


	def load_pretrained_config(self):

		f = open(os.sep.join([self.pretrained_model,"config_input.json"]))
		data = json.load(f)
		channels = data["channels"]
		signal_length = data["model_signal_length"]
		try:
			label = data['label']
			self.class_name_le.setText(label)
		except:
			pass
		self.model_length_slider.setValue(int(signal_length))
		self.model_length_slider.setEnabled(False)

		for c,cb in zip(channels, self.ch_norm.channel_cbs):
			index = cb.findText(c)
			cb.setCurrentIndex(index)

		if len(channels)<len(self.ch_norm.channel_cbs):
			for k in range(len(self.ch_norm.channel_cbs)-len(channels)):
				self.ch_norm.channel_cbs[len(channels)+k].setCurrentIndex(0)
				self.ch_norm.channel_cbs[len(channels)+k].setEnabled(False)
		self.ch_norm.add_col_btn.setEnabled(False)


	def adjustScrollArea(self):
		
		"""
		Auto-adjust scroll area to fill space 
		(from https://stackoverflow.com/questions/66417576/make-qscrollarea-use-all-available-space-of-qmainwindow-height-axis)
		"""

		step = 5
		while self.scroll_area.verticalScrollBar().isVisible() and self.height() < self.maximumHeight():
			self.resize(self.width(), self.height() + step)

	def _write_instructions(self):

		model_name = self.modelname_le.text()
		pretrained_model = self.pretrained_model
		signal_length = self.model_length_slider.value()
		recompile_op = self.recompile_option.isChecked()

		channels = []
		for i in range(len(self.ch_norm.channel_cbs)):
			channels.append(self.ch_norm.channel_cbs[i].currentText())

		slots_to_keep = np.where(np.array(channels)!='--')[0]
		while '--' in channels:
			channels.remove('--')

		norm_values = np.array([[float(a.replace(',','.')),float(b.replace(',','.'))] for a,b in zip([l.text() for l in self.ch_norm.normalization_min_value_le],
											[l.text() for l in self.ch_norm.normalization_max_value_le])])
		norm_values = norm_values[slots_to_keep]
		norm_values = [list(v) for v in norm_values]

		clip_values = np.array(self.ch_norm.clip_option)
		clip_values = list(clip_values[slots_to_keep])
		clip_values = [bool(c) for c in clip_values]

		normalization_mode = np.array(self.ch_norm.normalization_mode)
		normalization_mode = list(normalization_mode[slots_to_keep])
		normalization_mode = [bool(m) for m in normalization_mode]

		data_folders = []
		if self.dataset_folder is not None:
			data_folders.append(self.dataset_folder)
		if self.dataset_cb.currentText()!='--':
			dataset = locate_signal_dataset(self.dataset_cb.currentText())
			data_folders.append(dataset)

		aug_factor = self.augmentation_slider.value()
		val_split = self.validation_slider.value()

		try:
			lr = float(self.lr_le.text().replace(',','.'))
		except:
			msgBox = QMessageBox()
			msgBox.setIcon(QMessageBox.Warning)
			msgBox.setText("Invalid value encountered for the learning rate.")
			msgBox.setWindowTitle("Warning")
			msgBox.setStandardButtons(QMessageBox.Ok)
			returnValue = msgBox.exec()
			if returnValue == QMessageBox.Ok:
				return None			
		
		bs = int(self.bs_le.text())
		epochs = self.epochs_slider.value()

		training_instructions = {'model_name': model_name,'pretrained': pretrained_model, 'channel_option': channels, 'normalization_percentile': normalization_mode,
		'normalization_clip': clip_values,'normalization_values': norm_values, 'model_signal_length': signal_length,
		'recompile_pretrained': recompile_op, 'ds': data_folders, 'augmentation_factor': aug_factor, 'validation_split': val_split,
		'learning_rate': lr, 'batch_size': bs, 'epochs': epochs, 'label': self.class_name_le.text(), 'neighborhood_of_interest': self.current_neighborhood, 'reference_population': self.reference_population, 'neighbor_population': self.neighbor_population}

		model_folder = self.signal_models_dir +os.sep+ model_name + os.sep
		if not os.path.exists(model_folder):
			os.mkdir(model_folder)

		training_instructions.update({'target_directory': self.signal_models_dir})

		print(f"Set of instructions: {training_instructions}")
		with open(model_folder+"training_instructions.json", 'w') as f:
			json.dump(training_instructions, f, indent=4)
		
		# self.instructions = model_folder+"training_instructions.json"
		# process_args = {"instructions": self.instructions} # "use_gpu": self.use_gpu
		# self.job = ProgressWindow(TrainSignalModelProcess, parent_window=self, title="Training", position_info=False, process_args=process_args)
		# result = self.job.exec_()
		# if result == QDialog.Accepted:
		# 	pass
		# elif result == QDialog.Rejected:
		# 	return None	

		train_signal_model(model_folder+"training_instructions.json")
		self.parent_window.refresh_signal_models()
	
	def _load_previous_instructions(self):
		pass