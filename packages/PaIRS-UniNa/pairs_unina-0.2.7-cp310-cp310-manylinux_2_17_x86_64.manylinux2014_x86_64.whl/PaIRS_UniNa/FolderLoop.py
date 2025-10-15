import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QSpacerItem,
    QPushButton, QProgressBar, QSizePolicy,
    QFileDialog, QListView, QAbstractItemView, QTreeView,  QFileSystemModel
)
from PySide6.QtGui import QPixmap, QFont, QIcon, QCursor
from PySide6.QtCore import Qt, QTimer, QSize, QVariantAnimation
from time import sleep as timesleep
from pathlib import Path
from typing import Optional, List
from .PaIRS_pypacks import fontPixelSize, fontName, icons_path

time_sleep_loop=0

def choose_directories(base:Path = Path('.'),parent=None) -> Optional[List[str]]:
    """
    Open a dialogue to select multiple directories
    Args:
        base (Path): Starting directory to show when opening dialogue
    Returns:
        List[str]: List of paths that were selected, ``None`` if "cancel" selected"
    References:
        Mildly adapted from https://stackoverflow.com/a/28548773
        to use outside an exising Qt Application
    """
    
    file_dialog = QFileDialog(parent)
    file_dialog.setWindowTitle("Select folders for process loop")
    file_dialog.setWindowIcon(QIcon(icons_path + "process_loop.png"))
    file_dialog.setWindowIconText("Select folders for process loop")
    file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    file_dialog.setFileMode(QFileDialog.Directory)
    for widget_type in (QListView, QTreeView):
        for view in file_dialog.findChildren(widget_type):
            if isinstance(view.model(), QFileSystemModel):
                view.setSelectionMode(
                    QAbstractItemView.ExtendedSelection)

    paths=[]
    if file_dialog.exec():
        paths = file_dialog.selectedFiles()
        return paths
    
class FolderLoopDialog(QDialog):
    def __init__(self, pixmap_list, name_list, flag_list, parent=None, func=lambda it, opt:  print(f"Iteration {it}"),  paths=[], process_name = 'Process', *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        
        self.func=func
        self.nfolders=len(paths)
        self.paths=paths

        # Variables for easy customization
        self.setWindowTitle("Process loop over folders")
        self.setWindowIcon(QIcon(icons_path + "process_loop.png"))
        self.setWindowIconText("Process loop over folders")
        self.title_text = "Configure each step of the process"
        if parent is None:
            self.title_font = QFont(fontName, fontPixelSize+12, QFont.Bold)
            self.item_font = QFont(fontName, fontPixelSize+8)
            self.button_font = QFont(fontName, fontPixelSize+2)
        else:
            self.title_font:QFont = parent.font()
            self.title_font.setBold(True)
            self.title_font.setPixelSize(fontPixelSize+12)
            self.item_font:QFont = parent.font()
            self.item_font = parent.font()
            self.item_font.setPixelSize(fontPixelSize+8)
            self.button_font: QFont = parent.font()
            self.button_font.setPixelSize(fontPixelSize+2)
        self.title_height = 48
        self.icon_size = QSize(42, 42)  # Icon size inside buttons
        self.icon_size_off = QSize(24, 24)  # Icon size inside buttons when unchecked
        self.button_size = QSize(56, 56)  # Button size
        self.row_spacing = 18  # Spacing between rows
        self.margin_size = 5  # Window margin size
        self.progress_bar_height = 36
        
        self.min_height = self.row_spacing + self.margin_size*2 + self.title_height *2 + self.progress_bar_height   # min window height
        self.max_height = len(name_list) * (self.button_size.height() + self.row_spacing) + self.min_height # Max window height

        # Tooltip texts
        self.tooltips = {
            "copy": "Copy the item",
            "link": "Link the item",
            "change_folder": "Change the folder"
        }

        # Icons for the buttons
        self.icons = {
            "copy": [QIcon(icons_path + "copy_process.png"), QIcon(icons_path + "copy_process_off.png")],
            "link": [QIcon(icons_path + "link.png"), QIcon(icons_path + "unlink.png")],
            "change_folder": [QIcon(icons_path + "change_folder.png"), QIcon(icons_path + "change_folder_off.png")]
        }
        self.options_list=list(self.icons)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(self.row_spacing)

        # Left-aligned title
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0,0,0,0)
        header_layout.setSpacing(10)

        self.header_icon = QLabel('')
        self.header_icon.setPixmap(QPixmap(icons_path + "process_loop.png"))
        self.header_icon.setScaledContents(True)
        self.header_icon.setFixedSize(self.icon_size)
        header_layout.addWidget(self.header_icon)

        self.header_label = QLabel(process_name)
        self.header_label.setFont(self.title_font)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.header_label.setFixedHeight(self.title_height)
        header_layout.addWidget(self.header_label)

        layout.addLayout(header_layout)

        # Left-aligned title
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0,0,0,0)
        title_layout.setSpacing(10)

        """
        self.title_icon = QLabel('')
        self.title_icon.setPixmap(QPixmap(icons_path + "process_loop.png"))
        self.title_icon.setScaledContents(True)
        self.title_icon.setFixedSize(self.icon_size)
        title_layout.addWidget(self.title_icon)
        """

        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(self.title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setFixedHeight(self.title_height)
        title_layout.addWidget(self.title_label)
        
        layout.addLayout(title_layout)

        # List to store button states (0, 1, 2)
        self.button_states = [0] * len(name_list)

        # Add the additional n elements
        self.buttons_group = []
        self.step_options = []
        self.widgets = []
        self.nstep=len(pixmap_list)
        for i in range(self.nstep):
            widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(0,0,0,0)
            widget.setLayout(item_layout)
            widget.setFixedHeight(self.button_size.height())
            self.widgets.append(widget)

            # Label with pixmap (fitted to 32x32 pixels)
            pixmap_label = QLabel(self)
            pixmap = QPixmap(pixmap_list[i])#.scaled(self.button_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setScaledContents(True)
            pixmap_label.setFixedSize(self.button_size)
            item_layout.addWidget(pixmap_label)

            spacer=QSpacerItem(10, 0, QSizePolicy.Minimum, QSizePolicy.Minimum)
            item_layout.addItem(spacer)

            # Label with text from the name list (larger font)
            name_label = QLabel(name_list[i],self)
            name_label.setFont(self.item_font)
            name_label.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
            item_layout.addWidget(name_label)

            # Stretch the name label to fill the row
            item_layout.addStretch()

            # Three checkable buttons with icons
            self.step_options.append(-1)
            copy_button = self.create_icon_button(i, "copy")
            link_button = self.create_icon_button(i, "link")
            if flag_list[i]:
                folder_button = self.create_icon_button(i, "change_folder")
            else:
                folder_button = QLabel(self,text='')
                folder_button.setFixedWidth(self.button_size.width())
            self.buttons_group.append([copy_button, link_button, folder_button])
            
            item_layout.addWidget(copy_button)
            item_layout.addWidget(link_button)
            item_layout.addWidget(folder_button)

            layout.addWidget(widget)

        # Progress bar and final buttons (Cancel, Proceed)
        progress_widget = QWidget()
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0,0,0,0)
        progress_layout.setSpacing(10)
        progress_widget.setLayout(progress_layout)
        progress_widget.setFixedHeight(self.progress_bar_height)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.progress_bar.setVisible(False)  # Hidden initially
        self.title_label.adjustSize()
        self.progress_bar.setFixedWidth(self.title_label.width())
        progress_layout.addWidget(self.progress_bar)

        # Spacer to extend before the buttons
        progress_layout.addStretch()

        cancel_button_text = "Cancel"
        self.proceed_button_text = "Proceed"
        self.stop_button_text = "Stop"

        cancel_button = QPushButton(cancel_button_text,self)
        cancel_button.setFixedHeight(self.progress_bar_height)
        cancel_button.setFont(self.button_font)
        cancel_button.clicked.connect(self.cancel)  # Closes the dialog without doing anything
        progress_layout.addWidget(cancel_button)

        self.proceed_button = QPushButton(self.proceed_button_text,self)
        self.proceed_button.setFixedHeight(self.progress_bar_height)
        self.proceed_button.setFont(self.button_font)
        self.proceed_button.clicked.connect(self.on_proceed)
        progress_layout.addWidget(self.proceed_button)

        layout.addWidget(progress_widget)
        self.setLayout(layout)

        # Set window maximum height and margins
        self.setFixedHeight(self.max_height)
        self.setContentsMargins(self.margin_size*2, self.margin_size, self.margin_size*2, self.margin_size)

        # Timer for progress
        self.iteration = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.setSingleShot(True)
        self.loop_running = False

        self.animation=None

    def create_icon_button(self, index, button_type):
        """Create a checkable button with icon based on its type (copy, link, change_folder)."""
        button = QPushButton(self)
        button.setCheckable(True)
        button.setChecked((button_type=='change_folder' and index==self.nstep-1) or (button_type=='copy' and index<self.nstep-1))
        button.setIcon(self.icons[button_type][int(not button.isChecked())])  # Set initial 'off' icon
        button.setFixedSize(self.button_size)  # Set button size to 32x32 pixels
        button.setStyleSheet("QPushButton{border: none;}")  # Remove button borders
        button.setCursor(QCursor(Qt.PointingHandCursor))  # Set cursor to pointing hand on hover
        button.setToolTip(self.tooltips[button_type])  # Set tooltip
        button.clicked.connect(lambda: self.update_buttons(index, button_type))
        if button.isChecked():
            self.step_options[index]=self.options_list.index(button_type)
            button.setIconSize(self.icon_size)
        else:
            button.setIconSize(self.icon_size_off)  # Set icon size to 28x28 pixels
        return button

    def update_buttons(self, index, button_type):
        """Update the icons and states of the buttons, ensuring only one is checked at a time."""
        for k, button in enumerate(self.buttons_group[index]):
            if not isinstance(button,QPushButton): continue
            if  button_type!=self.options_list[k]:
                button.setChecked(False)  # Uncheck all buttons
                button.setIconSize(self.icon_size_off)
                button.setIcon(self.icons[self.options_list[k]][1])
            else:
                button.setChecked(True)
                button.setIconSize(self.icon_size)
                button.setIcon(self.icons[self.options_list[k]][0])  # Checked state icon
                self.step_options[index]=k

    def on_proceed(self):
        """Start or stop the progress loop depending on the button state."""
        if not self.loop_running:
            self.start_progress()
        else:
            self.stop_progress()

    def start_progress(self):
        """Start the progress and update button text to 'Stop'."""
        self.loop_running = True
        self.title_label.setText('Preparing copy...')
        self.title_label.setFont(self.item_font)
        self.proceed_button.setText(self.stop_button_text)
        self.proceed_button.setVisible(False)
        self.animate_window_resize()
        self.progress_bar.setVisible(True)  # Show the progress bar when Proceed is clicked
        self.progress_bar.setMaximum(self.nfolders)

    def stop_progress(self):
        """Stop the progress and update button text to 'Proceed'."""
        self.loop_running = False
        self.proceed_button.setText(self.proceed_button_text)
        self.timer.stop()

    def update_progress(self):
        """Update the progress bar on each timer tick."""
        if self.iteration < self.progress_bar.maximum():
            timesleep(time_sleep_loop)
            self.title_label.setText(self.paths[self.iteration])
            self.func(self.iteration,self.step_options)
            self.progress_bar.setValue(self.iteration)
            self.iteration += 1
            if self.loop_running: self.timer.start(0) 
        else:
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.stop_progress()
            if not self.animation: self.done(0)  # Closes the dialog when complete

    def cancel(self):
        if self.loop_running: self.stop_progress()
        if not self.animation: self.done(0)  # Closes the dialog when complete

    def animate_window_resize(self):
        for w in self.widgets:
            w:QWidget
            w.setVisible(False)
        self.animation = QVariantAnimation(self)
        self.animation.valueChanged.connect(self.window_resize)  
        self.animation.setDuration(300)
        self.animation.setStartValue(self.max_height)
        self.animation.setEndValue(self.min_height)
        self.animation.finished.connect(self.finishedAnimation)
        self.animation.start()

    def finishedAnimation(self):
        self.animation=None
        self.timer.start(0)  # Start or resume the timer

    def window_resize(self, h):
        self.setFixedHeight(h)

if __name__ == "__main__":
    import random
    import string

    # Function to generate a random string
    def generate_random_string(length):
        letters = string.ascii_letters  # Includes uppercase and lowercase letters
        return ''.join(random.choice(letters) for i in range(length))

    # Number of strings and length of each string
    num_strings = 10  # Number of strings in the list
    string_length = 25  # Length of each string

    # Generate the list of random strings
    random_strings_list = [generate_random_string(string_length) for _ in range(num_strings)]


    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    time_sleep_loop=0.01

    print(choose_directories())

    # Example lists
    pixmap_list = [icons_path + "cal_step.png",
                   icons_path + "min_step.png", 
                   icons_path + "disp_step.png", 
                   icons_path + "piv_step.png"]
    flag_list = [False,True,True,True]
    name_list = ["Camera calibration",
                 "Image pre-processing", 
                 "Disparity correction", 
                 "Stereoscopic PIV analysis"]

    dialog = FolderLoopDialog(pixmap_list, name_list, flag_list, paths=random_strings_list, process_name='Stereoscopic PIV process 1')
    sys.exit(dialog.exec())
