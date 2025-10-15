from celldetective.utils import get_software_location
from PyQt5.QtGui import QIcon
import os

class Styles(object):

	def __init__(self):

		self.init_button_styles()
		self.init_tab_styles()
		self.init_label_styles()

		self.help_color = "#1958b7" 

		
		self.celldetective_blue = "#1565c0"
		self.celldetective_logo_path = os.sep.join([get_software_location(),'celldetective','icons','logo.png'])
		self.celldetective_icon = QIcon(self.celldetective_logo_path)

		self.action_lbl_style_sheet = """
			font-size: 10px;
			padding-left: 10px;
			"""

	def init_button_styles(self):


		self.button_style_sheet = '''
			QPushButton {
				background-color: #1565c0;
				color: white;
				border-radius: 13px;
				padding: 7px;
				font-weight: bold;
				font-size: 12px;
			}
			QPushButton:hover {
				background-color: #2070EB;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}

			QPushButton:!enabled {
				background-color: #92a8c0;
				color: white;
				border-radius: 13px;
				padding: 7px;
				font-weight: bold;
				font-size: 12px;
			}
		'''

		self.button_style_sheet_2 = '''
			QPushButton {
				background-color: transparent;
				border: 3px solid #1565c0;
				color: #1565c0;
				border-radius: 15px;
				padding: 7px;
				font-weight: bold;
				font-size: 12px;
			}
			QPushButton:hover {
				background-color: #ecf0f1;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}

			QPushButton:disabled {
				border: 3px solid rgba(21, 101, 192, 0.50);
				color: rgba(21, 101, 192, 0.50);
			}

		'''

		self.button_style_sheet_5 = '''
			QPushButton {
				background-color: transparent;
				border: 3px solid #1565c0;
				color: #000000;
				border-radius: 15px;
				padding: 7px;
				font-size: 12px;
			}
			QPushButton:hover {
				background-color: #ecf0f1;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}

			QPushButton:disabled {
				border: 3px solid rgba(21, 101, 192, 0.50);
				color: rgba(21, 101, 192, 0.50);
			}

		'''


		self.button_style_sheet_2_not_done = '''
			QPushButton {
				background-color: transparent;
				border: 3px solid #d14334;
				color: #d14334;
				border-radius: 15px;
				padding: 7px;
				font-weight: bold;
				font-size: 12px;
			}
			QPushButton:hover {
				background-color: #ecf0f1;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}
		'''

		self.button_style_sheet_3 = '''
			QPushButton {
				background-color: #eeeeee;
				color: black;
				border-radius: 10px;
				padding: 7px;
				font-size: 8px;
			}
			QPushButton:hover {
				color: white;
				background-color: #2070EB;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}
		'''

		self.button_select_all = '''
			QPushButton {
				background-color: transparent;
				color: black;
				border-radius: 15px;
				padding: 7px;
				font-size: 9px;
			}
			QPushButton:hover {
				background-color: #bdbdbd;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}
		'''

		self.menu_check_style = '''
			QCheckBox {
				font-size: 10px;
				padding-left: 10px;
				padding-top: 5px;
			}
			QCheckBox::indicator:unchecked:hover {
				background-color : rgba(189, 189, 189, 1);
				opacity : 0.3;
			}
		'''

		self.button_add = '''
			QPushButton {
				background-color: transparent;
				color: black;
				border-radius: 13px;
				padding: 7px;
				font-size: 12px;
				Text-align: left;
			}
			QPushButton:hover {
				background-color: #bdbdbd;
			}
			QPushButton:pressed {
				background-color: #ff8a00;
			}
		'''

	def init_tab_styles(self):

		self.qtab_style = """
			QTabWidget::pane {
			border: 1px solid #B8B8B8;
			background: white;
		}

		QTabWidget::tab-bar:top {
			top: 1px;
		}

		QTabWidget::tab-bar:bottom {
			bottom: 3px solid blue;
		}

		QTabWidget::tab-bar:left {
			right: 1px;
		}

		QTabWidget::tab-bar:right {
			left: 1px;
		}

		QTabBar::tab {
			border: 1px solid #B8B8B8;
		}

		QTabBar::tab:selected {
			background: white;
		}

		QTabBar::tab:!selected {
			background: silver;
		}

		QTabBar::tab:!selected:hover {
			background: #999;
		}

		QTabBar::tab:top:!selected {
			margin-top: 3px;
		}

		QTabBar::tab:bottom:!selected {
			margin-bottom: 3px;
		}

		QTabBar::tab:top, QTabBar::tab:bottom {
			min-width: 8ex;
			margin-right: -1px;
			padding: 5px 10px 5px 10px;
		}

		QTabBar::tab:top:selected {
			border-bottom: 4px solid #1565c0;
		}


		QTabBar::tab:top:last, QTabBar::tab:bottom:last,
		QTabBar::tab:top:only-one, QTabBar::tab:bottom:only-one {
			margin-right: 0;
		}

		QTabBar::tab:left:!selected {
			margin-right: 3px;
		}

		QTabBar::tab:right:!selected {
			margin-left: 3px;
		}

		QTabBar::tab:left, QTabBar::tab:right {
			min-height: 8ex;
			margin-bottom: -1px;
			padding: 10px 5px 10px 5px;
		}

		QTabBar::tab:left:selected {
			border-left-color: none;
		}

		QTabBar::tab:right:selected {
			border-right-color: none;
		}

		QTabBar::tab:left:last, QTabBar::tab:right:last,
		QTabBar::tab:left:only-one, QTabBar::tab:right:only-one {
			margin-bottom: 0;
		}
		"""

	def init_label_styles(self):

		self.block_title = '''
			font-weight: bold;
			padding: 0px;
		'''