#!/bin/python3
import os, sys, subprocess, time, logging
from datetime import datetime
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2
from resources.FotoPi_GUI import Ui_FotoPi

log_dir = "logs"

if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
        print(f"dir: '{log_dir}' successfully created")
    except Exception as e:
        print(f"error creating dir: '{log_dir}': {e}")
        sys.exit(1)

log_filename = os.path.join(log_dir, time.strftime("FotoPi_%H-%M_%d-%m-%Y.log"))

logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def handle_exception(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.error("Uncaught exception: %s", str(exc_value))


sys.excepthook = handle_exception


def shutdown_raspi():
    try:
        subprocess.run(['sudo', 'shutdown', 'now'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing command: {e}")


class MainWindow(QWidget, Ui_FotoPi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.settings = QSettings("FotoPi", "FotoPi")
        self.setWindowIcon(QIcon('resources/icon.png'))
        self.setWindowTitle("FotoPi-GUI")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_folder = os.path.join(script_dir, "images")
        self.image_folder = self.settings.value("image_folder", default_folder)
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

        self.setCursor(Qt.BlankCursor)

        self.current_page = 0
        self.images_per_page = 9
        self.cur_iso = "1600"  # default picamera2 = 400
        self.cur_shutter = "1/30"  # default picamera2 = 1/30
        self.saturation_value = 1.00
        self.contrast_value = 1.00
        self.sharpness_value = 1.00
        self.brightness_value = 1.00
        self.awb_value = "Auto"
        self.output_format = self.settings.value("capture_format", ".jpg")

        self.shutter_speeds = {
            "1": 1_000_000,
            "1/2": 500_000,
            "1/4": 250_000,
            "1/8": 125_000,
            "1/15": 66_666,
            "1/30": 33_333,
            "1/60": 16_666,
            "1/125": 8_000,
            "1/250": 4_000,
            "1/500": 2_000,
            "1/1000": 1_000
        }

        # init picamera2
        self.app = QApplication([])
        self.picam2 = Picamera2()
        preview_config = self.picam2.create_preview_configuration(main={"size": (1440, 1080)})
        self.picam2.configure(preview_config)
        self.qpicamera2 = QGlPicamera2(self.picam2, keep_ar=True)
        # (w, h) = self.picam2.stream_configuration("main")["size"]
        # set default iso & shutter to easily match with gui
        self.picam2.set_controls({
            "AeEnable": False,
            "AnalogueGain": float(self.cur_iso) / 100,
            "ExposureTime": self.shutter_speeds.get(self.cur_shutter)
        })
        self.picam2.start()
        self.shutter_label.setText(QCoreApplication.translate("FotoPi", self.cur_shutter, None))
        self.iso_label.setText(QCoreApplication.translate("FotoPi", self.cur_iso, None))

        self.overlay_blk = np.zeros((300, 400, 4), dtype=np.uint8)
        self.overlay_blk[::] = (0, 0, 0, 100)

        self.viewport_grid.addWidget(self.qpicamera2, 100)

        self.grid_overlay_enabled = False
        self.grid_lines = []

        QFontDatabase.addApplicationFont("resources/fonts/Vegur-Regular.otf")
        QFontDatabase.addApplicationFont("resources/fonts/Vegur-Bold.otf")
        QFontDatabase.addApplicationFont("resources/fonts/contl.ttf")
        QFontDatabase.addApplicationFont("resources/fonts/contb.ttf")
        QFontDatabase.addApplicationFont("resources/fonts/contm.ttf")

        self.font0 = QFont()
        self.font0.setPointSize(30)
        self.font0.setFamily("Vegur Bold")
        self.font0.setBold(True)
        self.font0.setKerning(True)
        self.font0.setStyleStrategy(QFont.PreferAntialias)

        self.font1 = QFont()
        self.font1.setPointSize(34)
        self.font1.setFamily("Vegur Bold")
        self.font1.setBold(True)
        self.font1.setKerning(True)
        self.font1.setStyleStrategy(QFont.PreferAntialias)

        self.font2 = QFont()
        self.font2.setPointSize(20)
        self.font2.setFamily("Continuum Medium")
        self.font2.setKerning(True)
        self.font2.setStyleStrategy(QFont.PreferAntialias)

        self.font3 = QFont()
        self.font3.setPointSize(50)
        self.font3.setFamily("Continuum Bold")
        self.font3.setBold(True)
        self.font3.setKerning(True)
        self.font3.setStyleStrategy(QFont.PreferAntialias)

        self.font4 = QFont()
        self.font4.setPointSize(34)
        self.font4.setFamily("Continuum Medium")
        self.font4.setKerning(True)
        self.font4.setStyleStrategy(QFont.PreferAntialias)

        self.iso_label.setFont(self.font1)
        self.iso_label.setStyleSheet("color: white;")

        self.shutter_label.setFont(self.font1)
        self.shutter_label.setStyleSheet("color: white;")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_and_date)
        self.timer.start(1000)

        self.exit_button.clicked.connect(self.close)
        self.capture_button.clicked.connect(self.capture_clicked)
        self.gallery_button.clicked.connect(self.open_gallery)
        self.options_button.clicked.connect(self.open_options)
        self.settings_button.clicked.connect(self.open_settings)
        self.qpicamera2.done_signal.connect(self.capture_finished)

        self.iso_menu = QMenu()
        self.iso_menu.setFont(self.font3)
        self.iso_menu.setStyleSheet("""
            QMenu {
                background-color: rgb(21, 29, 38);
                color: white;
                border: 5px solid #000000;
                border-radius: 5px;
                icon-size: 0px;
            }
            
            QMenu::item {
                padding: 24px 55px;
                white-space: nowrap;
                background-color: rgb(21, 29, 38);
                color: white;
            }
            
            QMenu::item:selected {
                background-color: #ff426a;
                color: #000000;
            }
            QMenu::item:hover {
                background-color: #ff426a;
            }
            """)
        self.iso_button.setMenu(self.iso_menu)
        self.iso_button.setLayoutDirection(Qt.RightToLeft)

        for isos in ["100", "200", "320", "400", "640", "800", "1600", "3200", "6400"]:
            self.iso_menu.addAction(isos)

        self.iso_menu.triggered.connect(self.iso_selected)
        self.iso_menu.aboutToShow.connect(lambda: self.iso_button.setEnabled(False))
        self.iso_menu.aboutToHide.connect(lambda: self.iso_button.setEnabled(True))

        self.shutter_menu = QMenu()
        self.shutter_menu.setFont(self.font3)
        self.shutter_menu.setStyleSheet("""
            QMenu {
                background-color: rgb(21, 29, 38);
                color: white;
                border: 5px solid #000000;
                border-radius: 5px;
                icon-size: 0px;
            }
            
            QMenu::item {
                padding: 24px 55px;
                white-space: nowrap;
                background-color: rgb(21, 29, 38);
                color: white;
            }
            
            QMenu::item:selected {
                background-color: #ff426a;
                color: #000000;
            }
            QMenu::item:hover {
                background-color: #ff426a;
            }
            """)
        self.shutter_button.setMenu(self.shutter_menu)
        self.shutter_button.setLayoutDirection(Qt.RightToLeft)

        for shutters in ["1", "1/2", "1/4", "1/8", "1/15", "1/30", "1/60", "1/125", "1/250", "1/500", "1/1000"]:
            self.shutter_menu.addAction(shutters)

        self.shutter_menu.triggered.connect(self.shutter_selected)
        self.shutter_menu.aboutToShow.connect(lambda: self.shutter_button.setEnabled(False))
        self.shutter_menu.aboutToHide.connect(lambda: self.shutter_button.setEnabled(True))

        self.custom_action = QAction("Custom...")
        self.custom_action.triggered.connect(self.custom_shutter_selected)
        self.shutter_menu.addAction(self.custom_action)

        self.left_overlay_blk = QWidget(self)
        self.left_overlay_blk.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        self.left_overlay_blk.setGeometry(0, 0, 150, 1080)
        self.right_overlay_blk = QWidget(self)
        self.right_overlay_blk.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        self.right_overlay_blk.setGeometry(1600, 0, 320, 1080)
        self.left_overlay_blk.hide()
        self.right_overlay_blk.hide()

        self.output_dropdown = QComboBox()
        self.output_dropdown.setLayoutDirection(Qt.LeftToRight)
        self.output_dropdown.setStyleSheet("""
                QComboBox {
                    background-color: rgba(255, 255, 255, 75);
                    color: white;
                    font-size: 28px;
                    border: none;
                    border-radius: 5px;
                    padding-left: 10px;
                }
                QComboBox::drop-down {
                    color: white;
                    border: none;
                    border-top-right-radius: 5px;
                    border-bottom-right-radius: 5px;
                }
                QComboBox::down-arrow {
                    image: url(none);
                }
                QComboBox QAbstractItemView {
                    background-color: rgba(44, 44, 44, 230);
                    border: none;
                    color: white;
                    selection-background-color: rgba(255, 255, 255, 60);
                    selection-color: white;
                    border-radius: 5px;
                }
            """)
        self.output_dropdown.addItems([".jpg", ".png", ".dng"])
        self.output_dropdown.setFixedHeight(50)
        self.output_dropdown.setFixedWidth(200)
        self.output_dropdown.setCurrentText(self.output_format)
        self.output_dropdown.currentTextChanged.connect(self.output_update)

    def darkOverlayShow(self):
        self.left_overlay_blk.show()
        self.right_overlay_blk.show()
        self.qpicamera2.set_overlay(self.overlay_blk)

    def darkOverlayHide(self):
        self.left_overlay_blk.hide()
        self.right_overlay_blk.hide()
        self.qpicamera2.set_overlay(None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.picam2.close()
            print("Escape pressed, closing app.")
            self.close()

    def update_time_and_date(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M"))
        self.date_label.setText(now.strftime("%d.%m.%Y"))

    def iso_selected(self, action):
        self.cur_iso = action.text()
        self.iso_label.setText(self.cur_iso)
        iso_value = int(self.cur_iso)
        self.set_iso(iso_value)

    def set_iso(self, iso_value):
        self.picam2.set_controls({
            "AeEnable": False,
            "AnalogueGain": float(iso_value) / 100
        })

        self.show_toast(f"ISO set to: {self.cur_iso}", duration=2000)

    # Shutter sel
    def shutter_selected(self, action):
        if action.text() == "Custom...":
            return
        self.cur_shutter = action.text()
        self.shutter_label.setText(self.cur_shutter + "s")

        exposure_us = self.shutter_speeds.get(self.cur_shutter)
        if exposure_us is not None:
            self.picam2.set_controls({"ExposureTime": exposure_us})
            self.show_toast(f"Shutter Speed set to: {self.cur_shutter}s", duration=2000)
        else:
            print(f"Shutter Speed {self.cur_shutter} not in list.")

    def custom_shutter_selected(self):
        self.darkOverlayShow()
        panel = QWidget(self)
        panel.setStyleSheet("""
            background-color: rgb(21, 29, 38);
        """)
        panel.setFixedSize(750, 750)
        panel.setLayoutDirection(Qt.LeftToRight)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)

        label = QLabel("Shutter Speed (in seconds):")
        label.setFont(self.font0)
        label.setStyleSheet("color: white;")
        label.setAlignment(Qt.AlignCenter)

        input_field = QLineEdit()
        input_field.setStyleSheet("background-color: white; padding: 10px; border-radius: 5px;")
        input_field.setFont(self.font1)
        input_field.setFixedHeight(60)

        ok_button = QPushButton("OK")
        ok_button.setFont(self.font4)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(self.font4)

        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        # Buttons for 0-9
        def button_click(number):
            current_text = input_field.text()
            input_field.setText(current_text + str(number))

        def backspace():
            current_text = input_field.text()
            input_field.setText(current_text[:-1])

        def apply_custom_shutter():
            value = input_field.text()
            try:
                seconds = float(value)
                exposure_us = int(seconds * 1_000_000)
                self.cur_shutter = value
                self.shutter_label.setText(self.cur_shutter + "s")
                self.picam2.set_controls({"ExposureTime": exposure_us})
                self.show_toast(f"Shutter Speed set to: {self.cur_shutter}s", duration=2000)
                self.darkOverlayHide()
                panel.deleteLater()
            except ValueError:
                self.show_toast("Please type in a valid decimal number, e.g. 25 or 0.5", duration=2000)

        def cancel_custom_shutter():
            self.darkOverlayHide()
            panel.deleteLater()

        ok_button.clicked.connect(apply_custom_shutter)
        cancel_button.clicked.connect(cancel_custom_shutter)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        button_texts = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('0', 3, 1)
        ]

        for text, row, col in button_texts:
            button = QPushButton(text)
            button.setFixedHeight(75)
            button.setFixedWidth(200)
            button.setFont(self.font4)
            button.setStyleSheet("background-color: #333; color: white; padding: 20px; border-radius: 5px;")
            button.clicked.connect(lambda _, t=text: button_click(t))
            grid_layout.addWidget(button, row, col)

        backspace_button = QPushButton("←")
        backspace_button.setFont(self.font4)
        backspace_button.setFixedHeight(75)
        backspace_button.setFixedWidth(200)
        backspace_button.setStyleSheet(
            "background-color: #943b35; color: white; padding: 20px; border-radius: 5px;")  # f44336
        backspace_button.clicked.connect(backspace)
        grid_layout.addWidget(backspace_button, 3, 2)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        button_layout = QHBoxLayout()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        spacer = QHBoxLayout()
        spacer_label = QLabel("")
        spacer_label.setFixedHeight(20)
        spacer.addWidget(spacer_label)

        layout.addWidget(label)
        layout.addWidget(input_field)
        layout.addLayout(button_layout)
        layout.addLayout(spacer)
        layout.addLayout(grid_layout)

        panel.setLayout(layout)
        panel.move(
            (1920 - panel.width()) // 2,
            (1080 - panel.height()) // 2
        )

        panel.show()
        input_field.setFocus()

    def capture_clicked(self):
        print(self.picam2.camera_controls)
        self.capture_button.setEnabled(False)
        selected_format = self.settings.value("capture_format", ".jpg")
        # logging.error(f"Format: :{selected_format}:")
        filename = self.get_next_filename(selected_format)
        # sf = self.qpicamera2.signal_done
        signal_with_filename = lambda job: self.capture_finished(job, filename)

        if selected_format == ".dng":
            cfg = self.picam2.create_still_configuration(raw={})
            self.picam2.switch_mode_and_capture_file(cfg, filename, name="raw", signal_function=signal_with_filename)
        else:
            cfg = self.picam2.create_still_configuration(main={})
            self.picam2.switch_mode_and_capture_file(cfg, filename, signal_function=signal_with_filename)

        # cfg = self.picam2.create_still_configuration()
        # filename = self.get_next_filename()

    # def create_thumbnail(image_path, thumb_folder="images/thumbnails", size=(350, 250)):
    #     if not os.path.exists(thumb_folder):
    #         os.makedirs(thumb_folder)
    #
    #     with Image.open(image_path) as img:
    #         img.thumbnail(size, Image.ANTIALIAS)
    #         base_name = os.path.basename(image_path)
    #         thumb_path = os.path.join(thumb_folder, base_name)
    #         img.save(thumb_path, format="JPEG", quality=50)
    #
    #     return thumb_path

    def capture_finished(self, job, filename):
        self.picam2.wait(job)
        # if job is not None:
        #     self.picam2.wait(job)
        # image_folder_path = self.settings.value("image_folder")
        base_filename = os.path.basename(filename)
        self.show_toast(f"Photo saved as: {base_filename}", duration=3000)
        self.capture_button.setEnabled(True)

    def get_next_filename(self, file_extension):
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

        supported_extensions = ('.jpg', '.jpeg', '.png', '.dng')
        existing_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(supported_extensions)]

        numbers = []
        for f in existing_files:
            parts = f.split("-")
            if len(parts) > 0 and parts[0].isdigit():
                numbers.append(int(parts[0]))

        next_number = max(numbers) + 1 if numbers else 1
        next_number_str = f"{next_number:03d}"

        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y-%H-%M")

        filename = f"{next_number_str}-{timestamp}{file_extension}"
        filepath = os.path.join(self.image_folder, filename)

        return filepath

    def open_gallery(self):
        self.current_page = 0
        # self.show_toast("Loading gallery, please wait...", duration=6000)
        # time.sleep(1)
        self.darkOverlayShow()
        self.show_gallery()

    def show_gallery(self):
        panel = QWidget(self)
        panel.setStyleSheet("""
            background-color: rgb(34, 47, 62);
            border-radius: 15px;
        """)
        panel.setFixedSize(1620, 1080)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(24)
        panel.setLayoutDirection(Qt.LeftToRight)

        folder = self.image_folder
        if not os.path.exists(folder):
            os.makedirs(folder)
        image_files = sorted(
            [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
            reverse=True
        )

        def closeBlkOverlay():
            self.darkOverlayHide()
            panel.hide()

        start_idx = self.current_page * self.images_per_page
        end_idx = start_idx + self.images_per_page
        page_images = image_files[start_idx:end_idx]

        def show_previous_page():
            if self.current_page > 0:
                self.current_page -= 1
                panel.hide()
                closeBlkOverlay()
                self.show_gallery()

        def show_next_page():
            self.current_page += 1
            panel.hide()
            self.show_gallery()

        def show_fullscreen_image(img_path, display_name):
            grid_widget.hide()
            fullscreen_widget.show()
            pixmap = QPixmap(img_path)
            fullscreen_name_label.setText(display_name)
            fullscreen_image.setPixmap(pixmap.scaled(1200, 960, Qt.KeepAspectRatio, Qt.FastTransformation))
            fullscreen_image.setAlignment(Qt.AlignCenter)
            back_close_button.setText("Back")
            next_button.hide()
            prev_button.hide()

        for idx, img_file in enumerate(page_images):
            img_path = os.path.join(folder, img_file)
            pixmap = QPixmap(img_path)

            if not pixmap.isNull():
                image_height = pixmap.height()
                font_size = int(image_height * 0.085)

                painter_pixmap = pixmap.copy()
                painter = QPainter(painter_pixmap)
                painter.setFont(QFont('Arial', font_size, QFont.Bold))

                base_name = os.path.splitext(img_file)[0]
                parts = base_name.split("-")
                if len(parts) >= 6:
                    num = parts[0]
                    time_str = f"{parts[4]}:{parts[5]}"
                    date_str = f"{parts[1]}.{parts[2]}.{parts[3]}"
                    display_name = f"{num} | {time_str} | {date_str}"
                else:
                    display_name = base_name

                padding = 15
                rec_height = font_size + 8 * padding
                text_rect = QRect(0, painter_pixmap.height() - rec_height, painter_pixmap.width(), rec_height)

                painter.setBrush(QColor(0, 0, 0, 127))
                painter.drawRect(text_rect)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignBottom, display_name)
                painter.end()

                img_container = QWidget()
                img_layout = QVBoxLayout()
                img_layout.setContentsMargins(5, 5, 5, 5)
                img_layout.setSpacing(5)

                img_label = QLabel()
                img_label.setPixmap(painter_pixmap.scaled(400, 286, Qt.KeepAspectRatio, Qt.FastTransformation))
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setCursor(Qt.PointingHandCursor)

                img_label.mousePressEvent = lambda event, path=img_path, name=display_name: show_fullscreen_image(path,
                                                                                                                  name)
                img_layout.addWidget(img_label)
                img_container.setLayout(img_layout)

                row = idx // 3
                col = idx % 3
                grid_layout.addWidget(img_container, row, col)

        grid_widget.setLayout(grid_layout)

        fullscreen_widget = QWidget()
        fullscreen_layout = QVBoxLayout()
        fullscreen_layout.setContentsMargins(5, 15, 5, 5)
        fullscreen_layout.setSpacing(10)

        fullscreen_image = QLabel()
        fullscreen_name_label = QLabel()
        fullscreen_name_label.setAlignment(Qt.AlignCenter)
        fullscreen_name_label.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        fullscreen_layout.addWidget(fullscreen_name_label)
        fullscreen_layout.addWidget(fullscreen_image)

        fullscreen_widget.setLayout(fullscreen_layout)
        fullscreen_widget.hide()

        nav_layout = QHBoxLayout()
        nav_layout.setAlignment(Qt.AlignCenter)
        nav_layout.setContentsMargins(35, 10, 35, 35)
        nav_layout.setSpacing(125)
        # Previous Button
        prev_icon = QIcon()
        prev_icon.addFile("resources/icons/left.png", QSize(), QIcon.Normal, QIcon.Off)
        prev_button = QPushButton("")
        prev_button.setIcon(prev_icon)
        prev_size = QSize(127, 73)
        prev_button.setIconSize(prev_size)
        prev_button.setFixedWidth(156)
        prev_button.setFixedHeight(73)
        prev_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(21, 29, 38);
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #466180;
            }
        """)
        prev_button.setFixedSize(184, 85)
        prev_button.clicked.connect(show_previous_page)
        nav_layout.addWidget(prev_button)

        back_close_button = QPushButton("Close")
        back_close_button.setFont(self.font4)
        back_close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        back_close_button.setFixedSize(184, 73)
        nav_layout.addWidget(back_close_button)

        # Next Button
        next_icon = QIcon()
        next_icon.addFile("resources/icons/right.png", QSize(), QIcon.Normal, QIcon.Off)
        next_button = QPushButton("")
        next_button.setIcon(next_icon)
        next_size = QSize(127, 73)
        next_button.setIconSize(next_size)
        next_button.setFixedWidth(156)
        next_button.setFixedHeight(73)
        next_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(21, 29, 38);
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #466180;
            }
        """)
        next_button.setFixedSize(184, 85)
        next_button.clicked.connect(show_next_page)
        nav_layout.addWidget(next_button)

        def back_or_close():
            if fullscreen_widget.isVisible():
                fullscreen_widget.hide()
                grid_widget.show()
                back_close_button.setText("Close")
                next_button.show()
                prev_button.show()
            else:
                closeBlkOverlay()
                panel.hide()

        back_close_button.clicked.connect(back_or_close)

        layout.addWidget(grid_widget)
        layout.addWidget(fullscreen_widget)
        layout.addLayout(nav_layout)

        panel.setLayout(layout)
        panel.move(
            (1920 - panel.width()) // 2,
            (1080 - panel.height()) // 2
        )

        panel.show()

    def open_options(self):
        self.darkOverlayShow()
        panel = QWidget(self)
        panel.setStyleSheet("""
            background-color: rgb(21, 29, 38);
        """)
        panel.setLayoutDirection(Qt.LeftToRight)
        panel.setFixedSize(900, 900)

        layout = QVBoxLayout()
        layout.setContentsMargins(35, 35, 35, 35)
        layout.setSpacing(25)

        options_title = QLabel("App Settings")
        options_title.setStyleSheet("color: white; font-size: 32px; font-weight: bold;")
        options_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(options_title)
        layout.addStretch()

        folder_layout = QVBoxLayout()
        folder_label = QLabel("Current image folder:")
        folder_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        folder_path_label = QLabel(self.image_folder)
        folder_path_label.setStyleSheet("color: white; font-size: 28px;")
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(folder_path_label)
        folder_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(folder_layout)

        select_folder_button = QPushButton("Select folder")
        select_folder_button.setFont(self.font4)
        select_folder_button.setFixedWidth(400)
        select_folder_button.clicked.connect(self.select_image_folder)
        select_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        folder_layout.addWidget(select_folder_button)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Raised)
        line.setStyleSheet("background-color: rgba(255,255,255,0.3);")
        line.setFixedHeight(2)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Raised)
        line2.setStyleSheet("background-color: rgba(255,255,255,0.3);")
        line2.setFixedHeight(2)

        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Raised)
        line3.setStyleSheet("background-color: rgba(255,255,255,0.3);")
        line3.setFixedHeight(2)

        layout.addStretch()
        layout.addWidget(line)
        layout.addStretch()

        toggles_layout = QVBoxLayout()
        toggles_layout.setAlignment(Qt.AlignCenter)
        toggles_layout.setSpacing(25)
        toggle1 = QCheckBox("Enable Grid Overlay")
        toggle1.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 28px;
            }
            QCheckBox:checked {
                color: white;
            }
            QCheckBox::indicator {
                border-radius: 5px;
                width: 50px;
                height: 50px;
                border: 2px solid black;
                background-color: #ff426a;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #000000;
                background-color: #42ffba;
                color: white;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #000000;
                background-color: #ff426a;
            }
        """)
        toggle1.setChecked(self.grid_overlay_enabled)
        toggle1.stateChanged.connect(self.toggle_grid_overlay)

        output_label = QLabel("Output format", self)
        output_label.setStyleSheet("color: white; font-size: 28px;")
        output_spacer = QLabel("")
        output_spacer.setFixedHeight(28)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dropdown)
        output_layout.addWidget(output_label)
        # output_layout.addWidget(output_spacer)

        # self.output_dropdown.currentIndexChanged.connect(self.output_update)

        # self.toggle2 = QCheckBox("YAPO - Yet Another Placeholder Option")
        # self.toggle2.setStyleSheet("""
        #     QCheckBox {
        #         color: white;
        #         font-size: 28px;
        #         font-weight: bold;
        #     }
        #     QCheckBox:checked {
        #         color: white;
        #     }
        #     QCheckBox::indicator {
        #         border-radius: 5px;
        #         width: 50px;
        #         height: 50px;
        #         border: 2px solid black;
        #         background-color: #ff426a;
        #     }
        #     QCheckBox::indicator:checked {
        #         border: 1px solid #000000;
        #         background-color: #42ffba;
        #         color: white;
        #     }
        #     QCheckBox::indicator:unchecked {
        #         border: 1px solid #000000;
        #         background-color: #ff426a;
        #     }
        # """)
        toggles_layout.addStretch()
        toggles_layout.addWidget(toggle1)
        toggles_layout.addStretch()
        toggles_layout.addLayout(output_layout)
        toggles_layout.addStretch()
        # toggles_layout.addWidget(self.toggle2)

        layout.addLayout(toggles_layout)

        layout.addStretch()
        layout.addWidget(line2)
        layout.addStretch()

        shutdown_sys_button = QPushButton("Shutdown System")
        shutdown_sys_button.setFixedHeight(75)
        shutdown_sys_button.setFixedWidth(400)
        shutdown_sys_button.setFont(self.font4)
        shutdown_sys_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        shutdown_sys_button.clicked.connect(shutdown_raspi)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(shutdown_sys_button)

        def closeBlkOverlay():
            self.darkOverlayHide()
            panel.hide()

        close_button = QPushButton("Save")
        close_button.setFixedHeight(75)
        close_button.setFont(self.font4)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        close_button.clicked.connect(closeBlkOverlay)
        btn_layout.addWidget(close_button)
        layout.addLayout(btn_layout)
        layout.addStretch()
        layout.addWidget(line3)
        layout.addStretch()

        copyright_thanks_layout = QVBoxLayout()
        # copyright
        copyright_label = QLabel("© 2025 FotoPi by xcruell")
        copyright_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        copyright_label.setStyleSheet("color: white; font-size: 20px;")
        # thanks to
        thanks_label = QLabel("Special thanks to Samy & Noah   ")
        thanks_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        thanks_label.setStyleSheet("color: white; font-size: 18px;")
        # empty spacer labels, easier than actual spacers lol
        empty_label = QLabel("")
        empty_label_2 = QLabel("")
        empty_label_3 = QLabel("")
        # version numba + icon
        ver_icon_layout = QGridLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/icon.png")
        icon_label.setPixmap(pixmap)
        icon_label.resize(pixmap.width(), pixmap.height())
        icon_label.setAlignment(Qt.AlignRight)

        version_label = QLabel("FotoPi v0.7.0")
        version_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        version_label.setStyleSheet("color: white; font-size: 20px;")

        copyright_thanks_layout.setSpacing(0)
        copyright_thanks_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        copyright_thanks_layout.addWidget(copyright_label)
        copyright_thanks_layout.addWidget(thanks_label)

        ver_icon_layout.addWidget(empty_label, 0, 0)
        ver_icon_layout.addWidget(icon_label, 0, 1)
        ver_icon_layout.addWidget(version_label, 0, 2)
        ver_icon_layout.addWidget(empty_label_2, 0, 3)
        ver_icon_layout.addLayout(copyright_thanks_layout, 0, 4)
        ver_icon_layout.addWidget(empty_label_3, 0, 5)

        layout.addLayout(ver_icon_layout)
        panel.setLayout(layout)
        panel.move(
            (1920 - panel.width()) // 2,
            (1080 - panel.height()) // 2
        )

        panel.show()

    def select_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select save path", self.image_folder)
        if folder:
            self.image_folder = folder
            self.settings.setValue("image_folder", self.image_folder)
            self.folder_path_label.setText(self.image_folder)
            self.show_toast(f"New image folder set to: \n{self.image_folder} ", duration=4000)

    def open_settings(self):
        self.darkOverlayShow()
        panel = QWidget(self)
        panel.setStyleSheet("""
            background-color: rgb(21, 29, 38);
        """)
        panel.setFixedSize(900, 900)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(10)

        top_container = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(10)

        left_spacer = QSpacerItem(50, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        settings_title = QLabel("Camera Settings")
        settings_title.setFont(self.font0)
        settings_title.setStyleSheet("color: white;")
        settings_title.setAlignment(Qt.AlignCenter)

        right_spacer = QSpacerItem(145, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        reset_button = QPushButton("↺")
        reset_button.setFixedSize(40, 40)
        reset_button.setFont(QFont("Arial", 20, QFont.Bold))
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #ff426a;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #ba3450;
            }
        """)

        top_layout.addWidget(reset_button)
        top_layout.addItem(right_spacer)
        top_layout.addWidget(settings_title)
        top_layout.addItem(left_spacer)
        top_layout.addStretch()
        top_container.setLayout(top_layout)
        layout.addWidget(top_container)

        def add_slider(label_text, min_val, max_val, value_attr_name, picamera_control_name):
            container = QWidget()
            h_layout = QHBoxLayout()
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(15)

            current_value = getattr(self, value_attr_name)
            slider_value = int(current_value * 100)

            label = QLabel(label_text)
            label.setStyleSheet("color: white; font-size: 24px;")
            label.setFixedWidth(130)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(min_val)
            slider.setMaximum(max_val)
            # logging.error(f"{label_text}: {slider_value}")
            if label_text == "Brightness":
                slider.setValue(0)
                value_label = QLabel("0.00")
            else:
                slider.setValue(slider_value)
                value_label = QLabel(f"{current_value:.2f}")

            value_label.setStyleSheet("color: white; font-size: 24px;")
            value_label.setFixedWidth(75)

            slider.setStyleSheet("""
                QSlider::handle:horizontal {
                    background: #5c5c5c;
                    border: 1px solid #3A3939;
                    width: 50px;
                    height: 50px;
                    margin: -10px 0;
                    border-radius: 15px;
                }
                QSlider::groove:horizontal {
                    background: #bbb;
                    height: 10px;
                    border-radius: 5px;
                }
                QSlider::sub-page:horizontal {
                    background: #ff426a;
                    border-radius: 5px;
                }
                """)
            slider.setFixedHeight(50)
            slider.setFixedWidth(400)
            slider.setInvertedAppearance(False)
            slider.setInvertedControls(False)
            slider.setLayoutDirection(Qt.LeftToRight)

            def update_label(value):
                float_value = value / 100
                value_label.setText(f"{float_value:.2f}")
                setattr(self, value_attr_name, float_value)
                try:
                    self.picam2.set_controls({picamera_control_name: float_value})
                except Exception as e:
                    print(f"Failed to set {picamera_control_name}: {e}")
                # print(f"{label_text} updated to {float_value:.2f}")

            slider.valueChanged.connect(update_label)

            slider.start_value = slider.value()

            def slider_pressed():
                slider.start_value = slider.value()

            def slider_released():
                current = slider.value()
                value_label.setText(f"{current / 100:.2f}")
                print(f"{label_text} set to: {current / 100:.2f}")
                self.show_toast(f"{label_text} set to: {current / 100:.2f}", duration=2000)

            def slider_action_triggered(action):
                if action in (QAbstractSlider.SliderPageStepAdd, QAbstractSlider.SliderPageStepSub):
                    QTimer.singleShot(0, lambda: print_slider_value())

            def print_slider_value():
                current = slider.value()
                value_label.setText(f"{current / 100:.2f}")
                # print(f"{label_text} set to: {current / 100:.2f}")
                self.show_toast(f"{label_text} set to: {current / 100:.2f}", duration=2000)

            slider.sliderPressed.connect(slider_pressed)
            slider.sliderReleased.connect(slider_released)
            slider.actionTriggered.connect(slider_action_triggered)

            h_layout.addWidget(value_label)
            h_layout.addWidget(slider)
            h_layout.addWidget(label)
            container.setLayout(h_layout)
            layout.addWidget(container)

            return slider, value_label

        self.saturation_slider, self.saturation_label = add_slider("Saturation", 0, 200, "saturation_value",
                                                                   "Saturation")
        self.contrast_slider, self.contrast_label = add_slider("Contrast", 0, 200, "contrast_value", "Contrast")
        self.sharpness_slider, self.sharpness_label = add_slider("Sharpness", 0, 200, "sharpness_value", "Sharpness")
        self.brightness_slider, self.brightness_label = add_slider("Brightness", -100, 100, "brightness_value",
                                                                   "Brightness")

        awb_container = QWidget()
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(15)

        value_label = QLabel("")
        value_label.setFixedWidth(75)

        self.awb_dropdown = QComboBox()
        self.awb_dropdown.setLayoutDirection(Qt.LeftToRight)
        self.awb_dropdown.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 75);
                color: white;
                font-size: 24px;
                border: none;
                border-radius: 5px;
                padding-left: 10px;
            }
            QComboBox::drop-down {
                color: white;
                border: none;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox::down-arrow {
                image: url(none);
            }
            QComboBox QAbstractItemView {
                background-color: rgba(44, 44, 44, 230);
                border: none;
                color: white;
                selection-background-color: rgba(255, 255, 255, 60);
                selection-color: white;
                border-radius: 5px;
            }
        """)
        self.awb_dropdown.addItems(["Auto", "Incandescent", "Tungsten", "Fluorescent", "Indoor", "Daylight", "Cloudy"])
        self.awb_dropdown.setCurrentText(self.awb_value)
        self.awb_dropdown.setFixedHeight(50)
        self.awb_dropdown.setFixedWidth(400)

        awb_label = QLabel("AWB")
        awb_label.setStyleSheet("color: white; font-size: 24px;")
        awb_label.setFixedWidth(130)

        h_layout.addWidget(value_label)
        h_layout.addWidget(self.awb_dropdown)
        h_layout.addWidget(awb_label)

        awb_container.setLayout(h_layout)
        layout.addWidget(awb_container)

        def reset_to_defaults():
            self.saturation_slider.setValue(100)
            self.contrast_slider.setValue(100)
            self.sharpness_slider.setValue(100)
            self.brightness_slider.setValue(0)
            self.awb_dropdown.setCurrentIndex(0)

            self.show_toast("All settings reset to defaults.", duration=2000)

        reset_button.clicked.connect(reset_to_defaults)

        def closeBlkOverlay():
            self.darkOverlayHide()
            panel.hide()

        close_button = QPushButton("Save")
        close_button.setFont(self.font4)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        close_button.setFixedHeight(75)
        close_button.setFixedWidth(225)
        close_button.clicked.connect(closeBlkOverlay)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(15)
        h_layout.addWidget(close_button)
        layout.addLayout(h_layout)

        self.awb_dropdown.currentIndexChanged.connect(self.awb_update)

        panel.setLayout(layout)
        panel.move(
            (1920 - panel.width()) // 2,
            (1080 - panel.height()) // 2
        )

        panel.show()

    def awb_update(self, index):
        try:
            self.picam2.set_controls({"AwbMode": index})
            self.awb_value = self.awb_dropdown.currentText()
            self.show_toast(f"AWB set to: {self.awb_value}", duration=2000)
        except Exception as e:
            print(f"Failed to set AWB mode: {e}")

    def update_value_label(self, value):
        self.value_label.setText(f"{value / 100:.2f}")

    def output_update(self, selected_text):
        try:
            # 1. Speichere die neue Auswahl dauerhaft
            self.settings.setValue("capture_format", selected_text)

            # 2. Aktualisiere die Instanzvariable (optional, aber gut für die Konsistenz)
            self.output_format = selected_text

            # 3. Informiere den Benutzer
            self.show_toast(f"Output format set to: {self.output_format}", duration=3000)
        except Exception as e:
            print(f"Failed to set output format: {e}")

    def toggle_grid_overlay(self, state):
        if state == Qt.Checked:
            self.grid_overlay_enabled = True
            self.add_grid_overlay()
            self.show_toast("Grid Overlay enabled", duration=2000)
        else:
            self.grid_overlay_enabled = False
            self.remove_grid_overlay()
            self.show_toast("Grid Overlay disabled", duration=2000)

    def add_grid_overlay(self):
        self.remove_grid_overlay()

        for i in range(1, 4):
            h_line = QFrame(self.qpicamera2)
            h_line.setFrameShape(QFrame.HLine)
            h_line.setFrameShadow(QFrame.Sunken)
            h_line.setStyleSheet("background-color: rgba(255,255,255,1);")
            h_line.setGeometry(0, i * self.height() // 4, self.width(), 2)
            h_line.show()
            self.grid_lines.append(h_line)

        for i in range(1, 4):
            v_line = QFrame(self.qpicamera2)
            v_line.setFrameShape(QFrame.VLine)
            v_line.setFrameShadow(QFrame.Sunken)
            v_line.setStyleSheet("background-color: rgba(255,255,255,1);")
            v_line.setGeometry(i * self.width() // 5, 0, 2, self.height())
            v_line.show()
            self.grid_lines.append(v_line)

    def remove_grid_overlay(self):
        for line in self.grid_lines:
            line.deleteLater()
        self.grid_lines.clear()

    def show_toast(self, message, duration=2000):
        toast = QLabel(message, self)
        toast.setStyleSheet("""
            background-color: rgba(50, 50, 50, 255);
            color: white;
            border-radius: 10px;
            padding: 10px;
            font-size: 42px;
        """)
        toast.setAlignment(Qt.AlignCenter)
        toast.adjustSize()
        x = (1920 - toast.width()) // 2
        y = 1080 - toast.height() - 50
        toast.setGeometry(x, y, toast.width(), toast.height())
        toast.show()

        QTimer.singleShot(duration, toast.deleteLater)

    # def close_all_open_widgets(self):
    #     for widget in self.findChildren(QWidget):
    #         if widget.isVisible():
    #             widget.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    # window.show()  # on for debugging (disable showFullScreen())
    window.showFullScreen()
    sys.exit(app.exec_())
