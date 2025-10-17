from PyQt5.QtWidgets import (QApplication, QProgressDialog, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, 
                             QMessageBox, QLineEdit, QHBoxLayout, QGroupBox, QCheckBox, QRadioButton, QSlider, QDialog, QDialogButtonBox,
                             QComboBox, QGridLayout, QSpinBox)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage, QMouseEvent, QColor, QDoubleValidator
from PyQt5.QtCore import Qt, QPoint, QRect, QFileInfo, QTimer, QEvent, QSize
from fabio.edfimage import EdfImage
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import numpy
import matplotlib.pyplot as plt
import string
from PIL import Image
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os
import copy
import time as timelib
from datetime import datetime
from datetime import timedelta
import numpy as np
import sys
import re
import argparse
import cv2
import matplotlib
import subprocess
import shutil
import tempfile
from typing import Iterable, Set, Tuple, Optional, Callable, List
from textwrap import dedent

import matplotlib.pyplot as plt

matplotlib.use('Agg')




# Mapeamento codec → extensão recomendada
CODEC_EXTENSIONS = {
    "mp4v": ".mp4",
    "avc1": ".mp4",
    "H264": ".mp4",
    "XVID": ".avi",
    "MJPG": ".avi",
    "DIVX": ".avi",
    "WMV1": ".avi",
    "WMV2": ".avi",
}

class CodecDialog(QDialog):
    def __init__(self, available_codecs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Escolher Codec de Vídeo")
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # Texto de instrução
        layout.addWidget(QLabel("Selecione o codec e a extensão para salvar o vídeo:"))

        # Combobox para codecs
        self.codec_combo = QComboBox()
        for codec in available_codecs:
            ext = CODEC_EXTENSIONS.get(codec, ".avi")
            self.codec_combo.addItem(f"{codec}  →  {ext}", (codec, ext))
        layout.addWidget(self.codec_combo)

        # Botões OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_selection(self):
        """Retorna (codec, extensão) escolhido pelo usuário"""
        return self.codec_combo.currentData()


class ImageCropper(QMainWindow):
    
    
    def __init__(self):
        
        super().__init__()
        self.drawing = False
        self.rect_start = QPoint()
        self.current_rect = QRect()
        self.original_image = None
        self.image = None
        self.pixmap = None        
        self.result_image = None
        self.ret = None
        
        
        self.initUI()

        


    def initUI(self):
        
        # self.test = True
        self.test = False
        # print("teste")
        
        
        self.setWindowTitle('Analysis Droplet Parameters')
        self.setGeometry(100, 100, 1200, 600)

        # Criar um widget central e configurar o layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Layout to images
        self.image_layout = QVBoxLayout()
        self.main_layout.addLayout(self.image_layout)


        # Create a QLabel to display the image
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)    # centraliza o pixmap
        self.image_label.setMinimumSize(320, 240)
        self.image_layout.addWidget(self.image_label)
        self.image_label.setMouseTracking(True)

        
        # --- Video Player Controls ---      
        # Layout de controles do player de vídeo (abaixo do vídeo)
        self.video_bar_time_layout = QVBoxLayout()
        self.image_layout.addLayout(self.video_bar_time_layout)
        
        # Layout de controles do player de vídeo (abaixo do vídeo)
        self.video_controls_layout = QVBoxLayout()
        self.image_layout.addLayout(self.video_controls_layout)
              
        # progress bar
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_bar_time_layout.addWidget(self.video_slider)
        self.video_slider.sliderMoved.connect(self.seek_video)     
        
        # show time 
        self.time_label = QLabel('00:00 / 00:00')
        self.video_bar_time_layout.addWidget(self.time_label)   
        
        self.info_labels_layout = QHBoxLayout()
        self.mouse_label = QLabel('Mouse: (0,0)')
        self.image_size_label = QLabel("Image size: 0 x 0")
        
        self.info_labels_layout.addWidget(self.mouse_label)
        self.info_labels_layout.addWidget(self.image_size_label)
        self.info_labels_layout.addStretch()


        self.video_bar_time_layout.addLayout(self.info_labels_layout)
       
        
        # self.video_bar_time_layout.addWidget(self.image_size_label)
        
        # Timer para reprodução de vídeo
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.next_frame)
        
        # Variáveis de controle de vídeo
        self.video = None  # cv2.VideoCapture
        self.fps = 0
        self.total_frames = 0
        self.current_frame = 0
        self.playing = False
        
        # botons line: Play, Pause, Stop
        self.video_buttons_layout = QHBoxLayout()
        self.video_controls_layout.addLayout(self.video_buttons_layout)
        
        # Create a button to load the image
        self.load_button = QPushButton('Load Video', self)
        self.video_buttons_layout.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_image)
        
        # Botões de controle
        self.play_button = QPushButton('Play')
        self.pause_button = QPushButton('Pause')
        self.stop_button = QPushButton('Stop')
        self.export_button = QPushButton('Export Video', self)        
        

        self.video_buttons_layout.addWidget(self.play_button)
        self.video_buttons_layout.addWidget(self.pause_button)
        self.video_buttons_layout.addWidget(self.stop_button)
        self.video_buttons_layout.addWidget(self.export_button)
        
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.stop_button.clicked.connect(self.stop_video)  
        self.export_button.clicked.connect(self.export_video_dialog)
          
        
        # Slider de velocidade (0.25x a 2.0x)
        self.speed_label = QLabel("Speed: 1.0x")
        self.video_controls_layout.addWidget(self.speed_label)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(25)   #  0.25x
        self.speed_slider.setMaximum(200)  #  2.0x
        self.speed_slider.setValue(100)    #  1.0x
        self.speed_slider.setTickInterval(25)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.video_controls_layout.addWidget(self.speed_slider)

        self.speed_slider.valueChanged.connect(self.update_speed)
        
        
                # === Painel de coordenadas do retângulo ===
        self.rect_group = QGroupBox("Rectangle Position and Size")
        self.rect_layout = QGridLayout()
        self.rect_group.setLayout(self.rect_layout)

        # Cria os 4 campos (x, y, largura, altura)
        self.rect_x_spin = QSpinBox()
        self.rect_y_spin = QSpinBox()
        self.rect_w_spin = QSpinBox()
        self.rect_h_spin = QSpinBox()

        # Rótulos
        self.rect_layout.addWidget(QLabel("X:"), 0, 0)
        self.rect_layout.addWidget(self.rect_x_spin, 0, 1)
        self.rect_layout.addWidget(QLabel("Y:"), 0, 2)
        self.rect_layout.addWidget(self.rect_y_spin, 0, 3)
        self.rect_layout.addWidget(QLabel("Width:"), 1, 0)
        self.rect_layout.addWidget(self.rect_w_spin, 1, 1)
        self.rect_layout.addWidget(QLabel("Height:"), 1, 2)
        self.rect_layout.addWidget(self.rect_h_spin, 1, 3)

        # Adiciona ao layout principal lateral
        self.video_controls_layout.addWidget(self.rect_group)

        # Limites padrão (atualizados quando o vídeo é carregado)
        for spin in [self.rect_x_spin, self.rect_y_spin, self.rect_w_spin, self.rect_h_spin]:
            spin.setRange(0, 9999)
            spin.setSingleStep(1)

        # Conectar mudanças dos campos ao redesenho do retângulo
        self.rect_x_spin.valueChanged.connect(self.update_rect_from_spinboxes)
        self.rect_y_spin.valueChanged.connect(self.update_rect_from_spinboxes)
        self.rect_w_spin.valueChanged.connect(self.update_rect_from_spinboxes)
        self.rect_h_spin.valueChanged.connect(self.update_rect_from_spinboxes)
        
        
        
        # Layout to controls
        self.controls_layout = QVBoxLayout()
        self.main_layout.addLayout(self.controls_layout)

        # Create a QLabel to display the resulting image
        self.result_label = QLabel(self)
        self.image_layout.addWidget(self.result_label)


        

        # Create a button to crop the image
        self.crop_button = QPushButton('Crop Image', self)
        self.controls_layout.addWidget(self.crop_button)
        self.crop_button.clicked.connect(self.crop_image)

        # Create a button to display image information
        self.info_button = QPushButton('Information of Video', self)
        self.controls_layout.addWidget(self.info_button)
        self.info_button.clicked.connect(self.show_image_info)
        
        # Input fields for three integers
        #Group to first integer
        self.int_group4 = QGroupBox("C (mg/ml)")
        self.int_layout4 = QVBoxLayout()
        self.int_group4.setLayout(self.int_layout4)
        self.int_input_label4 = QLabel('Type the value of concentration (mg/ml)', self)
        self.int_input4 = QLineEdit(self)
        self.int_output4 = QLabel('', self)
        self.int_layout4.addWidget(self.int_input_label4)
        self.int_layout4.addWidget(self.int_input4)
        self.int_layout4.addWidget(self.int_output4)
        self.controls_layout.addWidget(self.int_group4)

        # Input fields for three integers
        #Group to first integer
        self.int_group1 = QGroupBox("Pixel/mm")
        self.int_layout1 = QVBoxLayout()
        self.int_group1.setLayout(self.int_layout1)
        self.int_input_label1 = QLabel('Type the value of pixel/mm:', self)
        self.int_input1 = QLineEdit(self)
        self.int_output1 = QLabel('', self)
        self.int_layout1.addWidget(self.int_input_label1)
        self.int_layout1.addWidget(self.int_input1)
        self.int_layout1.addWidget(self.int_output1)
        self.controls_layout.addWidget(self.int_group1)

        # Group to second integer
        self.int_group2 = QGroupBox("Interval")
        self.int_layout2 = QVBoxLayout()
        self.int_group2.setLayout(self.int_layout2)
        self.int_input_label2 = QLabel('Type the value of frame interval:', self)
        self.int_input2 = QLineEdit(self)
        self.int_output2 = QLabel('', self)
        self.int_layout2.addWidget(self.int_input_label2)
        self.int_layout2.addWidget(self.int_input2)
        self.int_layout2.addWidget(self.int_output2)
        self.controls_layout.addWidget(self.int_group2)

        # Group to third integer
        self.int_group3 = QGroupBox("Time limit")
        self.int_layout3 = QVBoxLayout()
        self.int_group3.setLayout(self.int_layout3)
        self.int_input_label3 = QLabel('Type the value of time limit (s):', self)
        self.int_input3 = QLineEdit(self)
        self.int_output3 = QLabel('', self)
        self.int_layout3.addWidget(self.int_input_label3)
        self.int_layout3.addWidget(self.int_input3)
        self.int_layout3.addWidget(self.int_output3)
        self.controls_layout.addWidget(self.int_group3)

        # Button to process integers
        self.process_button = QPushButton('Analysis droplet parameters', self)
        self.controls_layout.addWidget(self.process_button)
        self.process_button.clicked.connect(self.calcule_size_drop)

        # Group to third integer
        self.str_group4 = QGroupBox("Root Name File")
        self.str_layout4 = QVBoxLayout()
        self.str_group4.setLayout(self.str_layout4)
        self.str_input_label4 = QLabel('Type the name of root files:', self)
        self.str_input4 = QLineEdit(self)
        self.str_output4 = QLabel('', self)
        self.str_layout4.addWidget(self.str_input_label4)
        self.str_layout4.addWidget(self.str_input4)
        self.str_layout4.addWidget(self.str_output4)
        self.controls_layout.addWidget(self.str_group4)

        # Create a button to choose the directory and upload an image
        self.load_directory_button = QPushButton('Sort edf files by time', self)
        self.controls_layout.addWidget(self.load_directory_button)
        self.load_directory_button.clicked.connect(self.sort_images_edf_time)

        #Create a button to choose the directory and upload an image
        self.load_directory_button = QPushButton('Sort edf files by size droplet ', self)
        self.controls_layout.addWidget(self.load_directory_button)
        self.load_directory_button.clicked.connect(self.sort_images_edf_size_drop)


        #Create a button to choose the directory and upload an image
        self.load_directory_button = QPushButton('Match files from samples and background', self)
        self.controls_layout.addWidget(self.load_directory_button)
        self.load_directory_button.clicked.connect(self.contate_sort_images_edf_size_drop)
    
        # Checkbox para opção extra
        self.check_option = QCheckBox("Print a PDF with images", self)
        self.check_option.setChecked(False)  # desmarcado por padrão
        self.controls_layout.addWidget(self.check_option)
     
        # Hook mouse events
        self.image_label.installEventFilter(self)
        
        
        if self.test: 
            self.load_image()
            self.int_input1.setText("45.") 
            self.int_input2.setText("1") 
            self.int_input3.setText("25") 
            self.int_input4.setText("1.0") 

        self.show()

    def load_image(self):
        
        
        if hasattr(self, "video") and self.video and self.video.isOpened():
            self.video.release()

        
        if self.test: 
            self.file_path = "/home/standard02/Documents/programming/python/bolhas/PyPI/drap/teste.mp4"
            # "/home/standard02/Documents/programming/python/bolhas/PyPI/drap/teste_completo.mp4" teste_bolha.mp4
            # self.file_path, _ = QFileDialog.getOpenFileName(self, 'Open Video', '', 'Videos (*.avi *.mp4 *.mov *.mkv *.wmv *.flv *.mpg *.mpeg *.3gp *.ogv .webm)')
        else:
            self.file_path, _ = QFileDialog.getOpenFileName(self, 'Open Video', '', 'Videos (*.avi *.mp4 *.mov *.mkv *.wmv *.flv *.mpg *.mpeg *.3gp *.ogv .webm)')
        
        if not self.file_path:
            QMessageBox.warning(self, 'Warning', 'No video selected.')
            return
        
        self.file_path = os.path.normpath(str(Path(self.file_path).expanduser().resolve()))
        self.video = cv2.VideoCapture(self.file_path)
        self.ret = None
        
        
        if not self.video.isOpened():
            QMessageBox.critical(self, 'Error', f'Could not open video:\n{self.file_path}')
            return    
              
        # self.file_path = os.path.normpath(self.file_path)
        # self.file_path = QFileInfo(self.file_path).fileName();
        # self.file_path = Path(self.file_path);
        # self.file_path = self.file_path.resolve();
        # self.file_path = os.path.normpath(self.file_path);
                
        rval, frame = self.video.read();
        
        if not rval or frame is None:
            QMessageBox.critical(self, 'Error', 'Could not read first frame from the video.')
            self.video.release()
            return
 
        # Converte o frame OpenCV (BGR → RGB) para QImage/QPixmap
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

        # Atualiza atributos de imagem
        self.original_image = qimg
        self.image = qimg.copy()
        self.pixmap = QPixmap.fromImage(self.image)
        self.image_label.setPixmap(self.pixmap) #show image
        self.image_label.adjustSize()
        self.original_image = self.pixmap.toImage()
        # self.image_label.setScaledContents(True)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(Qt.AlignCenter)

        
        self.image_width = self.pixmap.width()
        self.image_height = self.pixmap.height()
        self.update_rect_limits()

        self.current_rect = QRect() 
        self.update_image()         
        self.img_size = [frame.shape[1], frame.shape[0]]
        
        self.image_size_label.setText(f"Image size: {self.img_size[1]} × {self.img_size[0]}")
        
        # Limitar X e Y dentro dos limites da imagem
        self.rect_x_spin.setRange(0, self.img_size[0] - 1 )
        self.rect_y_spin.setRange(0, self.img_size[1] - 1 )

        # Limitar largura e altura para não ultrapassar o tamanho da imagem
        self.rect_w_spin.setRange(0, self.img_size[0] - self.rect_x_spin.value())
        self.rect_h_spin.setRange(0, self.img_size[1] - self.rect_y_spin.value())

        # Reseta variáveis de estado
        self.fps = int(self.video.get(cv2.CAP_PROP_FPS))
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration_sec = self.total_frames / self.fps if self.fps else 0
        self.current_frame = 0
        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.video_slider.setMaximum(max(0, self.total_frames - 1))        
        self.playing = False
        
        # Atualiza UI
        # self.update_time_label()
        # self.display_frame()
        # self.image = self.original_image.copy()
        # self.display_cv2_frame(frame)

 

    def play_video(self):
        
        if self.video is None:
            return
        self.playing = True
        # self.video_timer.start(int(1000 / self.fps))  # chama a cada frame
        speed_factor = self.speed_slider.value() / 100.0
        interval = max(1, int(1000 / self.fps / speed_factor))
        self.video_timer.start(interval)


    def pause_video(self):
        
        self.playing = False
        self.video_timer.stop()
        
        
    def stop_video(self):
        
        if self.video is None:
            return
        self.pause_video()
        self.current_frame = 0
        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.display_frame()
        self.video_slider.setValue(0)
        self.update_time_label()

        
    def keyPressEvent(self, event):
        
        if event.key() == Qt.Key_Space:
            if self.playing:
                self.pause_video()
            else:
                self.play_video()


    def next_frame(self):
        
        if self.video is None or not self.playing:
            return
        
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.video.read()
        
        if not ret:
            self.pause_video()
            return

        self.display_cv2_frame(frame)
        self.video_slider.setValue(self.current_frame)
        self.update_time_label()
        
        self.current_frame += 1
        
        if self.current_frame >= self.total_frames:
            self.stop_video()
        
       
        

    def display_frame(self):
        
        
        if self.video is None:
            return
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.video.read()
        if ret:
            self.display_cv2_frame(frame)

    def display_cv2_frame(self, frame):
        
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

        
        # GUARDA a imagem atual
        self.original_image = q_image
        self.image = q_image.copy()
        self.pixmap = QPixmap.fromImage(self.image)
        self.image_label.setPixmap(self.pixmap)
        self.image_label.adjustSize()
        self.image_label.setPixmap(self.pixmap)
        self.image_width = w
        self.image_height = h
        self.update_rect_limits()
        # self.update_image()




    def seek_video(self, frame_number):
        
        if self.video is None:
            return
        self.pause_video()
        self.current_frame = frame_number
        self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.display_frame()
        self.update_time_label()

    def update_time_label(self):
        
        current_time = self.current_frame / self.fps if self.fps else 0
        total_time = self.total_frames / self.fps if self.fps else 0
        time_str = f"{self.format_time(current_time)} min  / {self.format_time(total_time)} min ({current_time:.2f} s -  frame: {self.current_frame})"
        self.time_label.setText(time_str)

    def format_time(self, seconds):
        
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def update_speed(self):
        
        speed_factor = self.speed_slider.value() / 100.0
        self.speed_label.setText(f"Speed: {speed_factor:.2f}x")
        if self.playing:
            interval = max(1, int(1000 / self.fps / speed_factor))
            self.video_timer.setInterval(interval)


    def export_video_dialog(self):
        
        if self.video is None:
            print(f"Error: input file not found: {self.video}", file=sys.stderr)
            return
        
        available_codecs = self.detect_codecs()
        dlg = CodecDialog(available_codecs)
        if dlg.exec_() == QDialog.Accepted:
            codec, ext = dlg.get_selection()
            # print(f"â Codec escolhido: {codec}, ExtensÃ£o: {ext}")


            # fourcc = cv2.VideoWriter_fourcc(*codec)
            # out = cv2.VideoWriter("saida" + ext, fourcc, fps, (width, height))
        
        # DiÃ¡logo para escolher onde salvar o vÃ­deo
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Video As", "", f"Video Files {codec}")
        base, ext = os.path.splitext(self.file_path)
        out_ext = out_ext = os.path.splitext(save_path)[1].lower()

        if not save_path:
            return
        
        if not out_ext:
            out_ext = '.mp4'
            save_path = (save_path + out_ext)
            

        # Widgets para escolher parÃ¢metros
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Video Settings")
        layout = QVBoxLayout(dialog)

        # Frame inicial
        start_label = QLabel("Start Frame:")
        start_input = QLineEdit(str(self.current_frame))
        validator_start = QDoubleValidator(0.0, self.current_frame, 0)
        start_input.setValidator(validator_start)
        layout.addWidget(start_label)
        layout.addWidget(start_input)

        # Frame final
        end_label = QLabel("End Frame:")
        end_input = QLineEdit(str(self.total_frames - 1))
        validator_end = QDoubleValidator(0.0, self.total_frames - 1, 0)
        end_input.setValidator(validator_end)
        layout.addWidget(end_label)
        layout.addWidget(end_input)
        
        # OpÃ§Ãµes exclusivas de exporta
        option_label = QLabel("Choose export mode:")
        layout.addWidget(option_label)

        # Radio buttons
        keep_frames_radio = QRadioButton("Keep frames each second")
        reduce_time_radio = QRadioButton("Reduce total time")
        keep_frames_radio.setChecked(True)
        layout.addWidget(keep_frames_radio)
        layout.addWidget(reduce_time_radio)

        # keep decider when the frame will save
        keep_decider_label = QLabel("Keep frames each second:")
        keep_decider_input = QLineEdit(str(self.fps))
        validator_fps = QDoubleValidator(0.0, self.fps, 0)
        keep_decider_input.setValidator(validator_fps)
        layout.addWidget(keep_decider_label)
        layout.addWidget(keep_decider_input)
        
        change_final_time_label = QLabel("New total duration (seconds):")
        change_final_time_input = QLineEdit(f"{self.duration_sec:.2f}")
        validator_time = QDoubleValidator(0.0, self.duration_sec, 2)
        change_final_time_input.setValidator(validator_time)
        layout.addWidget(change_final_time_label)
        layout.addWidget(change_final_time_input)
        
        
        # Inicialmente esconde o segundo campo
        change_final_time_label.hide()
        change_final_time_input.hide()
        
        def toggle_fields():
            if keep_frames_radio.isChecked():
                keep_decider_label.show()
                keep_decider_input.show()
                change_final_time_label.hide()
                change_final_time_input.hide()
            else:
                keep_decider_label.hide()
                keep_decider_input.hide()
                change_final_time_label.show()
                change_final_time_input.show()
                
        # Conecta eventos
        keep_frames_radio.toggled.connect(toggle_fields)
        reduce_time_radio.toggled.connect(toggle_fields)
                  
        
        # keep_time_checkbox = QCheckBox("Keep Total Time")
        # keep_time_checkbox.setChecked(True)  # padrÃ£o: marcado
        # layout.addWidget(keep_time_checkbox)
        

        # BotÃµes
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)


       
        def on_accept():
            try:
                start_f = int(start_input.text())
                end_f = int(end_input.text())
                fps_keep = int(keep_decider_input.text())
                total_time = float(change_final_time_input.text())

                if reduce_time_radio.isChecked() and total_time > self.duration_sec:
                    self.show_message( "Error", "The final time of output video must be equal or less than the original duration.", level="error")
                    return
                

                self.export_video(
                    self.file_path,
                    save_path,
                    codec,
                    start_f,
                    end_f,
                    fps_keep,
                    self.ret,
                    total_time if reduce_time_radio.isChecked() else None,
                    None
                )
                dialog.accept()

            except ValueError:
                show_message(self, "Error", "Please enter valid numeric values.", level="error")

        # crop_rect=(100, 50, 400, 300)  
        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(dialog.reject)

        dialog.exec_()  
   
   
   
    def export_video (self, in_path, out_path, codec, cut_first=0, cut_last=0, keep_decider=None, crop_rect=None, change_final_time= None, to_drop=None,):
        
        video_in = cv2.VideoCapture(in_path)        
        
        
        if not video_in.isOpened():
            raise RuntimeError(f"Not was possible open {in_path}")
        
        total_frames = int(video_in.get(cv2.CAP_PROP_FRAME_COUNT))      
        fps_in = int(video_in.get(cv2.CAP_PROP_FPS))
        if fps_in <= 0:
            raise ValueError(f"Invalid FPS: {fps_in}")
        
        
        # crop limits 
        start = max(0, cut_first)
        end = cut_last if cut_last > 0 else total_frames
        end = max(start, end) - 1
        # print(start, end, total_frames)
        
        
        w_in = int(video_in.get(cv2.CAP_PROP_FRAME_WIDTH))
        h_in = int(video_in.get(cv2.CAP_PROP_FRAME_HEIGHT))
 
        
        if crop_rect is not None:
            x, y, w_out, h_out = crop_rect
            x = max(0, min(x, w_in - 1))
            y = max(0, min(y, h_in - 1))
            w_out = min(w_out, w_in - x)
            h_out = min(h_out, h_in - y)
            
        else:
            x, y = 0, 0
            w_out, h_out = w_in, h_in
            
        size = (abs(w_out), abs(h_out))

       
        if change_final_time is None:
            kept = 0
            for idx in range(start, end):
                if to_drop and idx in to_drop:
                    continue
                if keep_decider and idx % keep_decider != 0:
                    continue
                kept += 1

            if kept == 0:
                raise RuntimeError("No frames selected for export!")     
            
            total_considered = end - start
            fps_out = fps_in * (kept / total_considered)
                # print(f"FPS adjusted: {fps_in:.2f} â {fps_out:.2f} (keeped {kept}/{total_considered})")
        else:
            fps_out = 30
            total_considered = end - start
            total_frames = change_final_time * fps_out
            keep_decider = numpy.ceil(total_considered / total_frames)
            kept = 0
            for idx in range(start, end):
                if keep_decider and idx % keep_decider != 0:
                    continue
                kept += 1
            
        
        
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError(f"Invalid size: {size}")

        # temporary file (backup)
        out_ext = os.path.splitext(out_path)[1] or ".mp4"
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="cut_", suffix=out_ext, delete=False,
                                        dir=os.path.dirname(os.path.abspath(out_path))) as tmp:
            tmp_out_path = tmp.name

        # Inicializar VideoWriter (tentando codecs candidatos, como vocÃª jÃ¡ fazia)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(tmp_out_path, fourcc, fps_out, size)

        if not writer.isOpened():
            raise RuntimeError("Failed to open VideoWriter with codec {codec}")

        progress = QProgressDialog("Exporting video...", "Cancel", 0, kept, self)
        progress.setWindowTitle("Please wait")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)



        # Loop in frames
        idx = 0
        written = 0
        current_kept = 0
        
        while True:
            
            ret, frame = video_in.read()
            if not ret:
                break

            if idx < start:       # crop first N frames
                idx += 1
                continue
            if idx >= end:         # crop last N frames
                break
            if to_drop and idx in to_drop:  # descartar manualmente
                idx += 1
                continue
            if keep_decider and idx % keep_decider != 0:  # functions decide if keep
                idx += 1
                continue
            
            # Crop if exist rect
            if crop_rect is not None:
                frame = frame[y:y+h_out, x:x+w_out]

            if ret and change_final_time is not None:
                time_ms = video_in.get(cv2.CAP_PROP_POS_MSEC)
                time_sec = time_ms / 1000.0
                text = f"t = {time_sec:.2f} s"
    
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1.0
                thickness = 2

                color = (0, 255, 0)

                # Calcula o tamanho do texto (largura e altura)
                (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)


                h, w = frame.shape[:2]
                x = w - text_width - 20   # 20 px de margem direita
                y = 40                    # 40 px a partir do topo

                # Escreve o texto no frame
                cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)




            # save frame 
            writer.write(frame)
            written += 1
            idx += 1
            current_kept += 1
            
            progress.setValue(current_kept)
            QApplication.processEvents()            
            if progress.wasCanceled():
                print("Export canceled by user.")
                break


        video_in.release()
        writer.release()

        if not progress.wasCanceled():
            # change the last file 
            shutil.move(tmp_out_path, out_path)
            # print(f"Video exported in {out_path}, ({written} saves frames)")
            progress.setValue(kept)
        else:
            os.remove(tmp_out_path)
            
            
            
            
    def draw_square(self, event, x, y, flags, param, imagem):



        if event == cv2.EVENT_LBUTTONDOWN:
            # Primeiro clique → guarda o ponto inicial
            self.vertices = [(x, y)]
            self.drawing = True

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            # Se estiver arrastando, mostra o quadrado "dinâmico"
            img_copy = param.copy()
            cv2.rectangle(img_copy, self.vertices[0], (x, y), (255, 0, 0), 2)
            cv2.imshow("Video", img_copy)

        elif event == cv2.EVENT_LBUTTONUP:
            # Segundo clique → fecha o quadrado
            self.vertices.append((x, y))
            self.drawing = False
            cv2.rectangle(param, vertices[0], self.vertices[1], (255, 0, 0), 2)
            cv_imshow_safe("Video", param)

            # print(f"Rectangle of {self.vertices[0]} up to {self.vertices[1]}")
 
 
 
    def label_pos_to_image_pos(self, pos: QPoint):
        

        if self.pixmap is None or self.image is None:
            return None

        label_size = self.image_label.size()
        pixmap_size = self.pixmap.size()

        # Calcula o offset (bordas pretas) se a imagem estiver centralizada
        x_offset = max((label_size.width() - pixmap_size.width()) // 2, 0)
        y_offset = max((label_size.height() - pixmap_size.height()) // 2, 0)

        # Remove o deslocamento
        x = pos.x() - x_offset
        y = pos.y() - y_offset

        # Garante que está dentro da imagem
        if 0 <= x < pixmap_size.width() and 0 <= y < pixmap_size.height():
            return QPoint(x, y)
        else:
            return None

 
        
    def detect_codecs(self):
        
        codecs = self.list_ffmpeg_codecs()
        if codecs:
            return codecs
        else:
            return self.test_opencv_codecs(["mp4v", "XVID", "MJPG", "H264", "avc1", "DIVX"])
   
        
    def list_ffmpeg_codecs(self):
        try:
            result = subprocess.run(["ffmpeg", "-codecs"], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                    text=True)
            codecs = []
            for line in result.stdout.splitlines():
                if line.startswith(" "):  # linhas úteis
                    parts = line.split()
                    if len(parts) >= 2:
                        codecs.append(parts[1])
            return codecs
        except FileNotFoundError:
            # print("⚠️ FFmpeg não encontrado no sistema.")
            return []

    def test_opencv_codecs(self,codecs, output_dir="test_codecs"):
        
        os.makedirs(output_dir, exist_ok=True)
        fps = 10
        frame_size = (320, 240)
        frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)

        available = []
        for codec in codecs:
            filename = os.path.join(output_dir, f"test_{codec}.avi")
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(filename, fourcc, fps, frame_size)
            if writer.isOpened():
                writer.write(frame)
                writer.release()
                if os.path.exists(filename) and os.path.getsize(filename) > 0:
                    available.append(codec)
        return available
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        





    def sort_images_edf_time(self):

        self.root_file_gui = str(self.str_input4.text());

        if not self.root_file_gui:
            QMessageBox.warning(self, 'Warning', 'No root files name was filled:')
            return

        directory = QFileDialog.getExistingDirectory(self, 'Choose Directory with EDF Images');
        directory = directory + "/";
        directory = Path(directory);
        directory = directory.resolve();
        directory = os.path.normpath(directory);
        #file_path, _ = QFileDialog.getOpenFileName(self, 'Choose file with polynomio data', directory, 'Data files (*.dat *.txt *.csv)')
        if directory:

            set_file_1 = conc_scat_video(4,path = directory, root_name = self.root_file_gui);
            set_file_1.read_setfiles_edf(option = 1);


    def sort_images_edf_size_drop(self):

        self.root_file_gui = str(self.str_input4.text());

        if not self.root_file_gui:
            QMessageBox.warning(self, 'Warning', 'No root files name was filled:')
            return

        directory = QFileDialog.getExistingDirectory(self, 'Choose Directory with EDF Images');
        directory = directory + "/"

        directory = os.path.normpath(directory);
        file_path, _ = QFileDialog.getOpenFileName(self, 'Choose file with polynomio data', directory, 'Data files (*.dat *.txt *.csv)')
        file_path = Path(file_path);
        file_path = file_path.resolve();
        file_path = os.path.normpath(file_path);

        if directory:
            set_file_1 = conc_scat_video(5,path = directory, root_name = self.root_file_gui, input_file = file_path);
            set_file_1.read_setfiles_edf(option = 0);

    def contate_sort_images_edf_size_drop(self):
        
        
        if self.test: 
            directory = "/home/standard02/Documents/programming/python/bolhas/data/15-SY-30cm/edf-15-SY"
        else:
            directory = QFileDialog.getExistingDirectory(self, 'Choose (Samples) Directory with EDF Images');
            
        directory = directory + "/";
        directory = Path(directory);
        directory = directory.resolve();
        directory = os.path.normpath(directory);

        if self.test: 
            file_path = '/home/standard02/Documents/programming/python/bolhas/PyPI/drap/data/15SY-30cm_Video_time_size.csv'
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, 'Choose (Samples) file with polynomio data', directory, 'Data files (*.dat *.txt *.csv)');

        file_path = Path(file_path);
        file_path = file_path.resolve();
        file_path = os.path.normpath(file_path);


        if directory:

            set_file_1 = conc_scat_video(5,path = directory, input_file = file_path);
            set_file_1.read_setfiles_edf(option = 2);


        if self.test: 
            directory = "/home/standard02/Documents/programming/python/bolhas/data/15-SY-30cm/edf-files-buffer"
        else:
            directory = QFileDialog.getExistingDirectory(self, 'Choose (Background) Directory with EDF Images');
        directory = directory + "/";


        directory = Path(directory);
        directory = directory.resolve();
        directory = os.path.normpath(directory);
        
        
        if self.test: 
            file_path = "/home/standard02/Documents/programming/python/bolhas/PyPI/drap/data/water-without-absolute-intensity-30cm_Video_time_size.csv"
        else :
            file_path, _ = QFileDialog.getOpenFileName(self, 'Choose (Background) file with polynomio data', directory, 'Data files (*.dat *.txt *.csv)');

        file_path = Path(file_path);
        file_path = file_path.resolve();
        file_path = os.path.normpath(file_path);

        if directory:

            set_file_2 = conc_scat_video(5,path = directory, input_file = file_path);
            set_file_2.read_setfiles_edf(option = 2);

        concatene_files_scat_back(set_file_1, set_file_2);

    def eventFilter(self, obj, event):
        
        if obj == self.image_label and (self.original_image is not None):
            
            # Atualiza posição do mouse (mesmo sem clicar)
            if event.type() == QEvent.MouseMove:
                pos = event.pos()
                mapped = self.label_pos_to_image_pos(pos)
                if mapped:
                    self.mouse_label.setText(f"Mouse: ({mapped.x()}, {mapped.y()})")

            # Início do desenho do retângulo
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                mapped = self.label_pos_to_image_pos(event.pos())
                if mapped is not None:
                    self.drawing = True
                    self.rect_start = mapped
                    self.current_rect = QRect(self.rect_start, QSize())
                    self.update_image()  # desenha imediatamente, sem atualizar limites
                    self.update_spinboxes_from_rect()

            # Movimento do mouse durante o desenho
            elif event.type() == QEvent.MouseMove and getattr(self, "drawing", False):
                mapped = self.label_pos_to_image_pos(event.pos())
                if mapped is not None:
                    self.current_rect = QRect(self.rect_start, mapped).normalized()
                    self.update_image()  # redesenha em tempo real (não mexe nos spinboxes ainda)

            # Soltar o botão: finalize o desenho
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if getattr(self, "drawing", False):
                    # self.drawing = False
                    mapped = self.label_pos_to_image_pos(event.pos())
                    if mapped is not None:
                        self.current_rect = QRect(self.rect_start, mapped).normalized()
                        self.update_image()  # mantém o desenho visível
                        self.update_spinboxes_from_rect()  # atualiza campos
                        self.update_rect_limits()  # aplica os limites só no final
                        self.drawing = False

        return super().eventFilter(obj, event)



    def crop_image(self):
        
        if not hasattr(self, "original_image") or self.original_image is None:
            QMessageBox.warning(self, "Warning", "No image loaded.")
            return
        if not hasattr(self, "current_rect") or self.current_rect.isNull():
            QMessageBox.warning(self, "Warning", "No rectangle drawn.")
            return

        cropped_image = self.original_image.copy(self.current_rect)
        save_path = Path("data/image_cropped.png").resolve()
        os.makedirs(save_path.parent, exist_ok=True)
        cropped_image.save(str(save_path))
        self.save_rectangle_coordinates(self.current_rect)


    def show_image_info(self):
        
        # Extract information from image
        width = self.pixmap.width()
        height = self.pixmap.height()
        format_str = self.image.format()
        depth = self.image.depth()

        info = (f"Dimensions: {width}x{height}\n"
                f"Format: {format_str}\n"
                f"Color Depth: {depth} bits\n"
                f"Frame Rate: {self.fps} f/s\n"
                f"Number Total of Frames: {self.total_frames}\n"
                f"Time Total (s): {round(self.total_frames/self.fps)} ")

        QMessageBox.information(self, 'Information of Image', info)
        
        
    def show_error_message(self, title, message):
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    def calcule_size_drop(self):
        
        
        if self.check_option.isChecked():
            print_pdf = True
        else:
            print_pdf = False
        
        if hasattr(self,  'ret') and self.ret is not None:
            pass;
        else:
            QMessageBox.warning(self, '', 'No rectangle drawn for cropping. Please draw rectangle first and cut the image.')
            return;

        if (self.int_input1.text() and self.int_input2.text() and self.int_input3.text() and self.int_input4.text()):
            numbers = [(input_field.text()) for input_field in [self.int_input1, self.int_input2, self.int_input3, self.int_input4]];

            for output_field, number in zip([self.int_output1, self.int_output2, self.int_output3], numbers):
                output_field.setText(f'Number: {number}')
            
            set_file_1 = conc_scat_video(3, file_video =self.file_path, px_mm = float(numbers[0]) , step = int(numbers[1]), time_limit = int(numbers[2]), Co = float(numbers[3]), retangulo = self.ret, print_pdf = print_pdf);
            result_image = set_file_1.read_video();
            if result_image:
                self.result_image = QPixmap(result_image)
                self.image = self.result_image.toImage()
                self.result_label.setPixmap(QPixmap.fromImage(self.image))
                # self.result_label.setScaledContents(True)
        else:
            QMessageBox.warning(self, 'Warning', 'Please Fill the forms.')
            return;

    def update_rect_from_spinboxes(self):
        """Atualiza o retângulo quando o usuário muda os valores manualmente."""
        if not hasattr(self, "current_rect"):
            self.current_rect = QRect()

        # Se o usuário estiver desenhando, ignore alterações manuais temporariamente
        if getattr(self, "drawing", False):
            return
        
        if not hasattr(self, "pixmap") or self.pixmap.isNull():
            return
        
        img_width = self.pixmap.width()
        img_height = self.pixmap.height()

        x = self.rect_x_spin.value()
        y = self.rect_y_spin.value()
        w = self.rect_w_spin.value()
        h = self.rect_h_spin.value()

        #  Ajusta se ultrapassar a borda direita ou inferior
        if x + w > img_width:
            w = img_width - x
            self.rect_w_spin.blockSignals(True)
            self.rect_w_spin.setValue(w)
            self.rect_w_spin.blockSignals(False)

        if y + h > img_height:
            h = img_height - y
            self.rect_h_spin.blockSignals(True)
            self.rect_h_spin.setValue(h)
            self.rect_h_spin.blockSignals(False)

        # 🔹 Garante que x, y não fiquem fora da imagem
        if x < 0:
            x = 0
            self.rect_x_spin.blockSignals(True)
            self.rect_x_spin.setValue(0)
            self.rect_x_spin.blockSignals(False)

        if y < 0:
            y = 0
            self.rect_y_spin.blockSignals(True)
            self.rect_y_spin.setValue(0)
            self.rect_y_spin.blockSignals(False)

        # 🔹 Atualiza o retângulo e redesenha
        self.current_rect = QRect(x, y, w, h)
        self.update_image()

    
    
    def update_spinboxes_from_rect(self):
        """Atualiza os campos (x, y, largura, altura) com base no retângulo atual desenhado."""
        if not hasattr(self, "current_rect") or self.current_rect.isNull():
            return

        rect = self.current_rect

        # Evita loops infinitos de sinal: desliga os sinais temporariamente
        self.rect_x_spin.blockSignals(True)
        self.rect_y_spin.blockSignals(True)
        self.rect_w_spin.blockSignals(True)
        self.rect_h_spin.blockSignals(True)

        # Atualiza os valores dos campos com o retângulo atual
        self.rect_x_spin.setValue(rect.x())
        self.rect_y_spin.setValue(rect.y())
        self.rect_w_spin.setValue(rect.width())
        self.rect_h_spin.setValue(rect.height())

        # Reativa os sinais
        self.rect_x_spin.blockSignals(False)
        self.rect_y_spin.blockSignals(False)
        self.rect_w_spin.blockSignals(False)
        self.rect_h_spin.blockSignals(False)

    def update_rect_limits(self):
        

        if not hasattr(self, "pixmap") or self.pixmap.isNull():
            return
        
        # Se o usuário está desenhando, não interfere
        if getattr(self, "drawing", False):
            return

        img_width = getattr(self, "image_width", self.pixmap.width())
        img_height = getattr(self, "image_height", self.pixmap.height())

        x = self.rect_x_spin.value()
        y = self.rect_y_spin.value()
        w = self.rect_w_spin.value()
        h = self.rect_h_spin.value()

        # Define novos limites
        self.rect_x_spin.setRange(0, img_width - 1)
        self.rect_y_spin.setRange(0, img_height - 1)
        self.rect_w_spin.setRange(1, img_width - x)
        self.rect_h_spin.setRange(1, img_height - y)

        # Se os valores atuais de largura/altura ultrapassarem os limites, reduza automaticamente
        if x + w > img_width:
            self.rect_w_spin.setValue(img_width - x)
            self.rect_w_spin.blockSignals(True)
            self.rect_w_spin.setValue(img_width - x)
            self.rect_w_spin.blockSignals(False)

        if y + h > img_height:
            self.rect_h_spin.setValue(img_height - y)
            self.rect_h_spin.blockSignals(True)
            self.rect_h_spin.setValue(img_height - y)
            self.rect_h_spin.blockSignals(False)

        # Só atualiza o retângulo se o usuário não estiver desenhando com o mouse
        if not getattr(self, "drawing", False):
            self.current_rect = QRect(x, y, self.rect_w_spin.value(), self.rect_h_spin.value())
            self.update_image()



    def update_image(self, frame=None):
        
        if frame is not None:
            self.image = cv2_to_qimage(frame)
            self.original_image = self.image.copy()
        elif self.image is None and self.original_image is not None:
            self.image = self.original_image.copy()
        elif self.original_image is not None:
            self.image = self.original_image.copy()

        else:
            return

        painter = QPainter(self.image)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))

        
        if hasattr(self, "current_rect") and not self.current_rect.isNull():
            painter.drawRect(self.current_rect)
        painter.end()

        self.pixmap = QPixmap.fromImage(self.image)
        self.image_label.setPixmap(self.pixmap)

        
        
#         if self.original_image and self.pixmap:
#             
#             self.image = self.original_image.copy()  # Restore the original image
#             painter = QPainter(self.image)
#             painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
#             
#             if not self.current_rect.isNull():
#                 painter.drawRect(self.current_rect)
#                 
#             painter.end()
#             self.pixmap = QPixmap.fromImage(self.image)
#             self.image_label.setPixmap(self.pixmap)

    def save_rectangle_coordinates(self, rect):
        
        # Save vertex coordinates to a file
        # x1, y1 = rect.topLeft().x(), rect.topLeft().y()
        # x2, y2 = rect.bottomRight().x(), rect.bottomRight().y()        
        # self.ret = [x1, x2, y1,y2]
        
        
        x = self.current_rect.x()
        y = self.current_rect.y()
        w = self.current_rect.width()
        h = self.current_rect.height()
        self.ret = [x, y, w,h]
        coordinates = f"Vértice do Retângulo: ({x}, {y}), width ({w}, height {h})"

        # Save the coordinates to a text file
        save_path = "data/";
        save_path = Path(save_path);
        save_path = save_path.resolve();
        save_path = os.path.normpath(save_path);
        save_path = os.path.join(save_path, 'data_image_croped.txt');
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        if save_path:
            with open(save_path, 'w') as file:
                file.write(coordinates)
            QMessageBox.information(self, 'Save', f'Coordenates saved in: {save_path}')
            

class Data_edf:

    def __init__(self, file_in, date_in, ExposureTime_in):

        self.file_ = file_in;
        self.Date = date_in;
        self.ExposureTime = ExposureTime_in;


    def get_infos(self):

        file_out = self.file_;
        date_out = self.Date;
        ExposureTime_out = self.ExposureTime;

        return file_out, date_out, ExposureTime_out   
    
    

def delete_value_extrem(data_in):

    r_len = len(data_in);
    window = 10;
    _w = data_in[:,1]; _h = data_in[:,2];#_area = data_in[:,5];
    mask = numpy.ones((r_len), dtype=bool);


    for i_data in range(window, r_len):
        
        w = data_in[i_data][1];
        h = data_in[i_data][2];

        avg_w = numpy.mean(_w[i_data-window:i_data]);
        avg_h = numpy.mean(_h[i_data-window:i_data]);

        std_w = numpy.std(_w[i_data-window:i_data]);
        std_h = numpy.std(_h[i_data-window:i_data]);

        if w > (avg_w + 2*std_w) or w < (avg_w - 2*std_w) or h > (avg_h + 2*std_h) or h < (avg_h - 2*std_h):
            mask[i_data] = False;

    data_out = numpy.zeros(shape=(len(data_in[0]), mask.sum()))
    data_out[0,:] = data_in[mask,0];
    data_out[1,:] = data_in[mask,1];
    data_out[2,:] = data_in[mask,2];
    data_out[3,:] = data_in[mask,3];
    data_out[4,:] = data_in[mask,4];
    data_out[5,:] = data_in[mask,5];
    data_out[6,:] = data_in[mask,6];
    data_out[7,:] = data_in[mask,7];
    data_out[8,:] = data_in[mask,8];

    return numpy.transpose(data_out)


def plot_data(data_abs,data_1, data_2, data_3, data_4, data_5, coef_pol_w_1, coef_pol_h_1, coef_pol_area_1,  coef_pol_conc_1, name_file):



    plt.clf()
    x_adj_1 = numpy.linspace(min(data_abs), max(data_abs), len(data_abs))
    y_w_adj_1 = numpy.polyval(coef_pol_w_1, x_adj_1)
    y_h_adj_1 = numpy.polyval(coef_pol_h_1, x_adj_1)
    y_area_adj_1 = numpy.polyval(coef_pol_area_1, x_adj_1)
    y_conc_adj_1 = numpy.polyval(coef_pol_conc_1, x_adj_1)




    fig, (ax2, ax1) = plt.subplots(2);

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Semi-axes (mm)')
    ax1.grid(True)

    ax1.plot(data_abs, data_1,"bo",  label='width');# concentration edge 1 plot
    ax1.plot(data_abs,data_2, "ro", label='height'); # concentration edge 2 plot
    ax1.plot(x_adj_1, y_w_adj_1, color='darkmagenta', label='Adjusted polynomio w');
    ax1.plot(x_adj_1, y_h_adj_1, color='g', label='Adjusted polynomio h');
    
    ax1_conc = ax1.twinx()
    ax1_conc.set_ylabel("Relative Concentration (%)")
    # Exemplo fictício de curva de concentração proporcional à área (você pode mudar isso):
    ax1_conc.plot(data_abs, data_4, "go", label="concentration") # concentration edge plot
    ax1_conc.plot(x_adj_1, y_conc_adj_1, color='m', label='Adjusted polynomio C');
    # ax2_conc.legend(loc="upper right")    
    
    
    ax1.legend(loc="upper right")

    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Surface ($mm^2$)')
    ax2.grid(True)


    ax2.plot(data_abs,data_3, "mo", label='Surface');  # concentration area plot
    ax2.plot(x_adj_1, y_area_adj_1, color='k', label='Adjusted polynomio S');
    # ax2.legend(loc="upper left")
    
    ax2_vol = ax2.twinx()
    ax2_vol.set_ylabel("Volume (\u03bcL)")
    # Exemplo fictício de curva de concentração proporcional à área (você pode mudar isso):
    ax2_vol.plot(data_abs, data_5,  "o", color="gray", label="volume") # concentration edge plot

    
    handles1, labels1 = ax2.get_legend_handles_labels()
    handles2, labels2 = ax2_vol.get_legend_handles_labels()
    all_handles = handles1 + handles2
    all_labels = labels1 + labels2
    
    ax2.legend(all_handles, all_labels, loc="best") 



    # plt.legend()
    plt.tight_layout()
    #plt.show()

    plt.savefig(name_file)


def plot_data_adjus(data_abs, coef_pol_w_1, coef_pol_h_1, coef_pol_area_1, name_file):


    plt.clf()
    x_adj_1 = numpy.linspace(min(data_abs), max(data_abs), len(data_abs))
    y_w_adj_1 = numpy.polyval(coef_pol_w_1, x_adj_1)
    y_h_adj_1 = numpy.polyval(coef_pol_h_1, x_adj_1)
    y_area_adj_1 = numpy.polyval(coef_pol_area_1, x_adj_1)


    fig, (ax2, ax1) = plt.subplots(2);

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Semi-axes (mm)')
    ax1.grid(True)


    ax1.plot(x_adj_1, y_w_adj_1, color='darkmagenta', label='Adjusted polynomio w1');
    ax1.plot(x_adj_1, y_h_adj_1, color='g', label='Adjusted polynomio h1');

    ax1.legend(loc="upper right")

    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Surface ($mm^2$)')
    ax2.grid(True)

    ax2.plot(x_adj_1, y_area_adj_1, color='k', label='Adjusted polynomio area 1');

    ax2.legend(loc="upper right")



    plt.legend()
    plt.show()

    plt.savefig(name_file)


def concatene_files_scat_back(set_file_1, set_file_2):

    list_scat_back = numpy.empty((len(set_file_1.info_files_edf) , 2), dtype=object) ;
    list_back_size_avg_drop = numpy.empty((len(set_file_2.info_files_edf) , 2), dtype=object) ;


    i_file = 0; factor = 0.15;
    temp_info_files_edf = [];
    for _date_1 in set_file_1.info_files_edf:
        find_back_drop = False;
        for _date_2 in set_file_2.info_files_edf:
            if  (abs(_date_1['area_small'] - _date_2['area_small']) < (_date_1['area_small'] * factor)) and (abs(_date_1['area_big'] - _date_2['area_big']) < (_date_1['area_big'] * factor) ):
                list_scat_back[i_file,0] = _date_1['file'];
                list_scat_back[i_file,1] = _date_2['file'];
                find_back_drop = True;
                break;
        if not find_back_drop:
            temp_info_files_edf.append(set_file_1.info_files_edf[i_file]);
            list_scat_back[i_file,0] = _date_1['file'];
        i_file = i_file + 1;


    i_file = 0;
    for _date_2 in set_file_2.info_files_edf:
        list_back_size_avg_drop[i_file,0] = _date_2['file'];
        list_back_size_avg_drop[i_file,1] = (_date_2['area_big'] + _date_2['area_small']) / 2. ;
        i_file = i_file + 1;


    factor = 0.15;
    # max_area = max(_date_1["area_big"] for _date_1 in temp_info_files_edf)
    temp_name_file = numpy.array(list_scat_back[:,0]);
    for _date_1 in temp_info_files_edf:
        area_avg_1 = (_date_1['area_big'] + _date_1['area_small']) / 2. ;

        min_diff = float('inf');

        for i_file_back in range(0, len(list_back_size_avg_drop)):
            if abs(area_avg_1 -  float(list_back_size_avg_drop[i_file_back,1])) <= (min_diff):
                min_diff = abs(area_avg_1 -  float(list_back_size_avg_drop[i_file_back,1] ) );
                result = numpy.where(temp_name_file == _date_1['file']);
                i_file= result[0].tolist()
                list_scat_back[i_file,1] = list_back_size_avg_drop[i_file_back,0]


    i_files = 0;
    path_ = Path('data/');
    path_ = Path(path_);
    path_ = path_.resolve();
    path_ = os.path.normpath(path_);
    os.makedirs(os.path.dirname(path_), exist_ok=True)
    
    with open(os.path.join(path_, 'FINAL_data_scat_back.lis'), 'w') as w_file:
        w_file.write('FAKELD.RAD\n');
        pos = list_scat_back[i_files,0].find('_0_');
        str_ = list_scat_back[i_files,0];
        str_ = str_[0:pos];
        str_ = str_ +'_0_00002.RDN';
        w_file.write(str_ + '\n');
        
        for row in range(0, len(list_scat_back)):
            if list_scat_back[i_files,0] is not None:
                w_file.write('1\n');
                list_scat_back[i_files,0] = list_scat_back[i_files,0].replace('.edf', '.RAD')
                list_scat_back[i_files,1] = list_scat_back[i_files,1].replace('.edf', '.RAD')                
                str_ = f"{list_scat_back[i_files,0]}"
                w_file.write(str_ + '\n');
                str_ = f"{list_scat_back[i_files,1]}"
                w_file.write(str_ + '\n');
                w_file.write('1.00000000\n');
                list_scat_back[i_files,0] = list_scat_back[i_files,0].replace('.RAD', '.RDS');
                str_ = f"{list_scat_back[i_files,0]}"
                w_file.write(str_ + '\n');
                i_files = i_files + 1;

def calcule_concentration(edge_1, edge_2, Co, Vo):
    
       
    Vol_drop = calcule_vol_spheroide(edge_1, edge_2)  / 1000.
    
    return  (Co * Vo) / Vol_drop;
    

def calcule_vol_spheroide(edge_1, edge_2):
    
    
    if edge_1 == edge_2:  # sphere
        
        return  (4 / 3) * np.pi * edge_1**3    
    
    else : # oblate and prolate spheroid
        
           
        return  (4 / 3) * np.pi  * (edge_1**2) * edge_2 
   

        

def choose_funtion():

    options = {
        1: "Option 1: Analysis droplet parameters",
        2: "Option 2: Sort edf files by time",
        3: "Option 3: Sort edf files by size drop",
        4: "Option 4: Concatene edf samples and background files"
            }

    print("\nChoose one of the following options:\n")
    for key, description in options.items():
        print(f"{key}: {description}")

    while True:
        try:
            choice = int(input("\nEnter the number of your choice (1-4): "))
            if choice in options:
                print(f"\nYou chose, {options[choice]}")
                return choice
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def cv_imshow_safe(img_name, img):
    """Mostra imagem se HighGUI estiver disponível; caso contrário, ignora."""
    try:
        cv2.imshow(img_name, img)
        cv2.waitKey(1)
    except cv2.error:
        pass  # headless: sem suporte a janela

def cv_destroy_all_windows_safe():
    """Fecha janelas do OpenCV se suportado; caso contrário, ignora."""
    try:
        cv2.destroyAllWindows()
    except cv2.error:
        pass  # headless


def cv2_to_qimage(frame):
    
    """Converte frame do OpenCV (BGR) para QImage (RGB)."""
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    
    return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

def get_dir_paths( **kwargs):

    # Create a hidden Tkinter window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Prompt the user to choose the directory
    print('Choose Directory with EDF Images');
    directory = filedialog.askdirectory(title="\nChoose the directory to read edf files: ")

    while not directory:
        print("\nNo directory selected. Try again.")
        directory = filedialog.askdirectory(title="\nChoose the directory to read edf files: ")

    directory = Path(directory);
    directory = os.path.normpath(directory);

    get_file_path = False;
    file_path= '';
    if 'get_file_path' in kwargs:
        get_file_path = kwargs['get_file_path'];
    if get_file_path:
        print('Choose file with polynomio data');
        file_path = filedialog.askopenfilename(title="\nSelect a file with polynomio data: ")
        while not file_path:
            print("\nNo file name provided. Try again.")
            file_path = filedialog.askopenfilename(title="\nSelect a file with polynomio data: ")
    file_path = Path(file_path);
    file_path = file_path.resolve();
    file_path = os.path.normpath(file_path);

    get_file_root = False;
    root_file= '';
    if 'get_file_root' in kwargs:
        get_file_root = kwargs['get_file_root'];
    if get_file_root:
        root_file = str(input("\nType root output file name: "))
        root_file = root_file.replace('.', '')
        while not root_file:
            print("\n No file name provided. Try again.")
            root_file = str(input("\nType root output file name: "))
            root_file = root_file.replace('.', '')

    return directory, root_file, file_path



def get_info_video():


    questions = [
        "Type the interval between frames to get the drop size: ",
        "Type the START pixel value (left bottom), in the image in X EDGE, to select the drop region: ",
        "Type the START pixel value (left bottom), in the image in Y EDGE, to select the drop region: ",
        "Type the WIDTH value, in the image, to select the drop region: ",
        "Type the HEIGHT value, in the image, to select the drop region: ",
        "Type the value of pixel by millimeters: ",
        "Type the maximum video analysis time (s): "
    ]

    # Dictionary to store the answers
    answers = {}
    answers_out = numpy.zeros(shape=(7), dtype = int );

    print("\n Answer the following questions with integers greater than 0:")

    for i, question in enumerate(questions):
        while True:
            try:
                # Request user response
                answer = int(input(f"\n{i + 1}. {question} "))

                # Validates if the response is an integer greater than 0
                if answer > 0:
                    answers[question] = answer;
                    answers_out[i] = answer;
                    break
                else:
                    print("\nThe answer must be an integer greater than 0. Please try again.")
            except ValueError:
                print("\nInvalid input. Please enter an integer.")

    return answers_out

def get_video_file():

    file_extension = input("\nType the video file format (.avi .mp4 .mov .mkv .wmv .flv .mpg .mpeg .3gp .ogv .webm):  ").strip()

    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension

    # Get the list of files in the current directory
    current_directory = os.getcwd()
    files_in_directory = os.listdir(current_directory)

    # Filter files by the given extension
    filtered_files = [file for file in files_in_directory if file.endswith(file_extension)]

    # Creates a dictionary where the key is a number and the value is the file name
    files_dict = {i+1: file for i, file in enumerate(filtered_files)}

    # Print the list of filtered files with numbers
    if files_dict:
        print(f"\nFiles with the extension '{file_extension}' in the directory'{current_directory}'\n:")
        for number, file in files_dict.items():
            print(f"{number}: {file}")

        # Prompt the user to choose a file
        while True:
            try:
                choice = int(input("\nEnter the desired file number: "))
                if choice in files_dict:
                    print(f"Você escolheu o arquivo: {files_dict[choice]}")
                    return files_dict[choice]
                else:
                    print("\nInvalid number. Please enter a number from the list.")
            except ValueError:
                print("\nInvalid input. Please enter a number.")
    else:
        print(f"\nThere are no files with the extension '{file_extension}' in the directory '{current_directory}'.")


class conc_scat_video:

    def __init__(self, option, **kwargs):

        if 'file_in' in kwargs:
            file_in = kwargs['file_in'];

        if option  == 1:

            f_open = open(file_in, 'r');
            text = f_open.readlines();

            for line in text:
                if line.find('file_video_1:') != -1:
                    file_video = str(line[line.index(':')+1:line.index('.')+5]);
                    self.file_video = file_video.translate({ord(c): None for c in string.whitespace})
                    self.name_file = os.path.basename(self.file_video);
                    self.name_file = self.name_file[0:self.name_file.index('.')];
                    self.root_file =  self.name_file;
                if line.find('Co_1:') != -1:
                    self.Co = (float(str(line[line.index(':')+1:])));
                if line.find('step_1:') != -1:
                    self.step = round(float(str(line[line.index(':')+1:])));
                if line.find('left bottom pixel x_1:') != -1:
                    self.start_x = round(float(str(line[line.index(':')+1:])));
                if line.find('left bottom pixel y_1:') != -1:
                    self.start_y = round(float(str(line[line.index(':')+1:])));
                if line.find('width_1:') != -1:
                    self.width = round(float(str(line[line.index(':')+1:])));
                if line.find('height_1:') != -1:
                    self.height = round(float(str(line[line.index(':')+1:])));
                if line.find('pixel/mm_1:') != -1:
                    self.px_mm = (float(str(line[line.index(':')+1:])));
                    self.px_mm_inv = 1. / self.px_mm
                if line.find('directory_path_1:') != -1:
                    self.path = str(line[line.index(':')+1:]);
                    self.path = self.path.translate({ord(c): None for c in string.whitespace})
                    self.path = Path(self.path);
                    self.path = self.path.resolve();
                    self.path = os.path.normpath(self.path);
                if line.find('time_limit_1:') != -1:
                    self.time_limit = float(str(line[line.index(':')+1:]));
                if line.find('print_pdf_1:') != -1:
                    temp = str(line[line.index(':')+1:])
                    temp = temp.strip()
                    temp = temp.lower()
                    if temp == "y" or temp == "yes" :                        
                        self.print_pdf = True
                    else: 
                        self.print_pdf = False
            f_open.close();

        elif option  == 2:

            f_open = open(file_in, 'r');
            text = f_open.readlines();

            for line in text:
                if line.find('file_video_2:') != -1:
                    file_video = str(line[line.index(':')+1:line.index('.')+5]);
                    self.file_video = file_video.translate({ord(c): None for c in string.whitespace})
                    self.name_file = os.path.basename(self.file_video);
                    self.name_file = self.name_file[0:self.name_file.index('.')];
                    self.root_file =  self.name_file;
                if line.find('Co_2:') != -1:
                    self.Co = (float(str(line[line.index(':')+1:])));
                if line.find('step_2:') != -1:
                    self.step = round(float(str(line[line.index(':')+1:])));
                if line.find('left bottom pixel x_2:') != -1:
                    self.start_x = round(float(str(line[line.index(':')+1:])));
                if line.find('left bottom pixel y_2:') != -1:
                    self.start_y = round(float(str(line[line.index(':')+1:])));
                if line.find('width_2:') != -1:
                    self.width = round(float(str(line[line.index(':')+1:])));
                if line.find('height_2:') != -1:
                    self.height = round(float(str(line[line.index(':')+1:])));
                if line.find('pixel/mm_2:') != -1:
                    self.px_mm = (float(str(line[line.index(':')+1:])));
                    self.px_mm_inv = 1. / self.px_mm
                if line.find('directory_path_2:') != -1:
                    self.path = str(line[line.index(':')+1:]);
                    self.path = self.path.translate({ord(c): None for c in string.whitespace})
                    self.path = Path(self.path);
                    self.path = self.path.resolve();
                    self.path = os.path.normpath(self.path);
                if line.find('time_limit_2:') != -1:
                    self.time_limit = float(str(line[line.index(':')+1:]));
                if line.find('print_pdf_2:') != -1:
                    temp = str(line[line.index(':')+1:])
                    temp = temp.strip()
                    temp = temp.lower()
                    if temp == "y" or temp == "yes" :                        
                        self.print_pdf = True
                    else: 
                        self.print_pdf = False
                    
            f_open.close();
            if hasattr(self, 'file_video') and self.file_video is not None:
                if not os.path.exists(self.file_video):
                    print("ideo File 2 not found or not loaded:", self.file_video)  
                    exit(0);
            else:
                print("Video File 2 not found or not loaded.")  
                exit(0);

        elif option  == 3:

            if 'file_video' in kwargs:
                self.file_video = kwargs['file_video'];
                self.name_file = os.path.basename(self.file_video);
                self.name_file = self.name_file[0:self.name_file.index('.')];
            if 'Co' in kwargs:
                self.Co = float(kwargs['Co']);
            if 'px_mm' in kwargs:
                self.px_mm = float(kwargs['px_mm']);
                self.px_mm_inv = 1. / self.px_mm
            if 'step' in kwargs:
                self.step = kwargs['step'];
            if 'time_limit' in kwargs:
                self.time_limit = kwargs['time_limit'];
            if 'retangulo' in kwargs:
                ret = kwargs['retangulo'];
                self.start_x = ret[0];
                self.start_y = ret[1];
                self.width = ret[2];
                self.height = ret[3];
            if 'print_pdf' in kwargs:
                self.print_pdf = kwargs['print_pdf'];
            else:
                self.print_pdf = False;

        elif option  == 4 or option  == 5:
            if 'Co' in kwargs:
                self.Co = float(kwargs['Co']);
            if 'path' in kwargs:
                self.path = Path(kwargs['path']);
                self.path = self.path.resolve();
                self.path = os.path.normpath(self.path);
            if 'root_name' in kwargs:
                self.root_file = kwargs['root_name'];
            if 'input_file' in kwargs and option  == 5:
                input_file = kwargs['input_file'];
                self.coef_pol_w, self.coef_pol_h, self.coef_pol_area, self.coef_pol_conc, _ = read_file_video(input_file);



    def print_frames_pdf(self, path_dir_imgs, file_data_imgs):





        with open(file_data_imgs, mode='r') as file_data:
                lines = file_data.readlines();
                list_data_imgs= [["" for _ in range(2)] for _ in range(len(lines))]
                #list_data_imgs[len(rows),2];
                #next(_read)  # Ignorar o cabeçalho
                i_row = 0;
                for row in lines:
                    index = row.find(' ');
                    list_data_imgs[i_row][0] = row[0:index];
                    list_data_imgs[i_row][1] = row[index+1:];
                    i_row = i_row + 1;

        n_col = 4;
        n_row = 5;
        n_pages = 5;


        pdf_path = self.name_file+"_resume_imgs.pdf";
        # print(pdf_path)
        pdf_path = os.path.join(path_dir_imgs, pdf_path);
        # Create pdf file
        #pdf = SimpleDocTemplate(path_dir_imgs+"resume_imgs.pdf", pagesize=A4)
        pdf = canvas.Canvas(pdf_path, pagesize=A4)
        page_width, page_height = A4

        margin = 30
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin
        cell_width = available_width / 4
        cell_height = available_height / 5


        # Iterate over the images and add them to the PDF
        num_imagens = len(list_data_imgs)
        num_paginas = (num_imagens + 19) // 20  # 20 imagens por página (4x5)

        for pagina in range(num_paginas):

            # Add a new page
            pdf.showPage()

            # Calcular posição inicial da tabela
            y_inicio = page_height - margin
            x_inicio = margin

            # Draw the table (4 columns x 5 rows)
            for linha in range(5):
                for coluna in range(4):
                    indice_imagem = pagina * 20 + linha * 4 + coluna
                    if indice_imagem < num_imagens:
                        x = x_inicio + coluna * cell_width
                        y = y_inicio - linha * cell_height - cell_height
                        caminho_imagem = list_data_imgs[indice_imagem][0]
                        imagem = Image.open(caminho_imagem)
                        largura_imagem, altura_imagem = imagem.size
                        proporcao = largura_imagem / altura_imagem
                        largura_final = cell_width
                        altura_final = largura_final / proporcao
                        if altura_final > cell_height:
                            altura_final = cell_height
                            largura_final = altura_final * proporcao
                        pdf.drawImage(caminho_imagem, x, y, largura_final, altura_final)
                        try:
                            del imagem
                            os.remove(caminho_imagem)
                        except FileNotFoundError:
                            print(f"O arquivo não foi encontrado: {caminho_imagem}")

        pdf.save()


    def read_setfiles_edf(self, **kwargs):

        path_dir_imgs = Path('data/');
        path_dir_imgs = path_dir_imgs.resolve();
        path_dir_imgs =  os.path.normpath(path_dir_imgs);

        try :
            os.makedirs(path_dir_imgs);
        except :
            pass;

        if 'option' in kwargs:
            option = kwargs['option'];
        else:
            option = 2;

        if  option == 0:
            name_file = self.root_file+'_EDF_data_Size_Drop.csv'
        elif  option == 1:
            name_file = self.root_file+'_EDF_data_Time.csv'

        _files = os.listdir(self.path);
        format_time = '%Y-%m-%d %H:%M:%S'

        # Filter only files
        self._files_edf = [item for item in _files if os.path.isfile(os.path.join(self.path, item)) and item.lower().endswith('.edf')]



        self.info_files_edf = [];
        info_files_edf = [];

        i_file  = 0;
        for _file in self._files_edf:           

            edf_img = EdfImage().read(os.path.join(self.path, _file))
            header = edf_img.header;

            data = {'file': _file, 'date': datetime.strptime(header['Date'],format_time), 'time': header['ExposureTime'], 'start_time': 0  , 'end_time': 0, 'area_small': 0  , 
                    'area_big': 0, 'area':0, 'concentration':0,  'dropDX': 0, 'dropDY': 0}
            info_files_edf.append(data)

            self.info_files_edf = sorted(info_files_edf, key=lambda x: x['date'])


        date_time_0 = self.info_files_edf[0]['date'];
        for _date in self.info_files_edf:
            diff = _date['date'] - date_time_0;
            _date['start_time'] = diff.total_seconds();
            _date['end_time'] = diff.total_seconds() + float(_date['time']);
            if option == 1:
                _date['area_small'] = 0;
                _date['area_big'] = 0;
                _date['dropDX'] = 0.;
                _date['dropDY'] = 0;
            else:
                _date['area_small'] = numpy.polyval(self.coef_pol_area, _date['start_time']);
                _date['area_big'] = numpy.polyval(self.coef_pol_area, _date['end_time']);
                _date['area'] = abs(_date['area_big'] +  _date['area_small'])/ 2.;
                _date['concentration'] = abs(numpy.polyval(self.coef_pol_conc, _date['start_time']) +  numpy.polyval(self.coef_pol_conc, _date['end_time']) )/ 2.;
                _date['dropDX'] = abs(numpy.polyval(self.coef_pol_w, _date['start_time']) +  numpy.polyval(self.coef_pol_w, _date['end_time']) )/ 2.;
                _date['dropDY'] = abs(numpy.polyval(self.coef_pol_h, _date['start_time']) + numpy.polyval(self.coef_pol_h, _date['end_time'])) / 2.;

        if  option == 0 or option == 1:
            save_data_edf(self.info_files_edf, os.path.join(path_dir_imgs, name_file), option);


    def read_video(self):        
       

        # self.video_c = os.path.getctime(self.file_video);
        # print(self.file_video)
        

        self.video_m = os.path.getmtime(self.file_video);

        # read video
        video = cv2.VideoCapture(self.file_video)
        #AVI (.avi) MP4 (.mp4)MOV (.mov) MKV (.mkv) WMV (.wmv) FLV (.flv) MPEG (.mpg, .mpeg) 3GP (.3gp) OGG (.ogv) WEBM (.webm)

        if video.isOpened():
            rval , frame = video.read()
        else:
            rval = False

        # get Information about video
        fps = video.get(cv2.CAP_PROP_FPS);
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        max_frames = total_frames;

        size_data = int(total_frames /  self.step) + 1;
        if self.time_limit != 0:
            size_data = int(self.time_limit*fps /  self.step) + 1;
        else:
            self.time_limit = total_frames / fps;
        
        # set data matrix store data
        new_size_data = size_data;
        data_time_size = numpy.zeros(shape=(size_data, 9), dtype = float );
        temp_size_window = numpy.zeros(shape=(size_data, 2), dtype = float );
        
        # col1 = np.arange(0.8, 0.09, -0.05)
        # col2 = np.ones_like(col1)
        # col2 = 30* col2;
        # temp_m = np.column_stack((col1, col2))
        # flag_temp = 0;
        # print(temp_m)

        frame_count = 0
        saved_frame_count = 0
        data_i = 0;

        # set name and directory output files 
        path_dir_imgs = "data/";
        path_dir_imgs = Path(path_dir_imgs);
        path_dir_imgs = path_dir_imgs.resolve();
        path_dir_imgs = os.path.normpath(path_dir_imgs);

        file_image_str = os.path.join(path_dir_imgs, self.name_file+"_data_images.dat")
        os.makedirs(os.path.dirname(file_image_str), exist_ok=True)
        file_data_imgs = open(file_image_str, "w", encoding='utf-8');

        has_frame, frame = video.read();
        file_img = os.path.join(path_dir_imgs,self.name_file+'_sample_frame.jpg');
        cv2.imwrite(file_img,frame); #exit();

        # crop image to restrict background
        new_start_x = self.start_x;
        new_start_y = self.start_y;
        ref_end_x = new_end_x = self.start_x + self.width;
        ref_end_y = new_end_y = self.start_y + self.height;
        ref_width = abs(self.width);
        ref_height = abs(self.height);

        amplie = False;
        factor = 1;
        start_time = timelib.time()
        
        progress = ProgressHandler(self, label="Reading frames...", maximum=total_frames)

        while has_frame: # take frame just end of video

            if (frame_count / fps) > self.time_limit: break;
            img_h, img_w = frame.shape[:2];

            if frame_count % self.step == 0:
                time = frame_count / fps;
                time_str =  f"{time:.4f}";
                time_str = time_str.replace('.', '_')

                
                if data_i >= 1:
                    # reduce the area in image croped to reduce background noises
                    area = abs(new_end_x - new_start_x) * abs(new_end_y - new_start_y);
                    x_start = self.start_x + abs(self.start_x - new_start_x) + (x_start/factor);
                    y_start = self.start_y + abs(self.start_y - new_start_y) + (y_start/factor);
                    x_center = int((x_start + (x_start + width))/ 2.)
                    y_center = int((y_start + (y_start + height))/ 2.)

                    # if size of drop reduce the image croped reduce
                    if ( (width * height) < 0.2 * area or (ref_width - width) < 0.15 * ref_width or (ref_height - height) < 0.15 * ref_height   ):
                        if data_i > 200:
                            window = 200;
                        else:
                            window = data_i;
                            
                        _w = temp_size_window[data_i-window:data_i,0]; _h = temp_size_window[data_i-window:data_i,1];
                        avg_w = numpy.mean(_w) ;
                        avg_h = numpy.mean(_h) ;
                        if avg_w < 0.15* abs(ref_end_x - self.start_x): avg_w = 0.15 * abs(ref_end_x - self.start_x);
                        if avg_h < 0.15* abs(ref_end_y - self.start_y): avg_h =0.15 *abs(ref_end_y - self.start_y);
                        factor_exp = 0.15;
                        new_start_x = int(( x_center - avg_w/2) - (factor_exp * avg_w));
                        new_end_x = int(( x_center + avg_w/2) + (factor_exp * avg_w));
                        if new_start_x < self.start_x: new_start_x = self.start_x;
                        if new_end_x > ref_end_x:  new_end_x = ref_end_x;
                        ref_width = abs(new_end_x - new_start_x);
                        new_start_y =  int(( y_center - avg_h/2) - (factor_exp * avg_h));
                        new_end_y =  int(( y_center + avg_h/2) + (factor_exp * avg_h));
                        if new_start_y < self.start_y: new_start_y = self.start_y;
                        if new_end_y > ref_end_y: new_end_y = ref_end_y;
                        ref_height = abs(new_end_y - new_start_y);
                        amplie = True;


                # print(new_start_y,new_end_y, new_start_x,new_end_x, " ")
                # cv2.imwrite("teste.png",frame); #exit();
                #crop image
                imagem = frame[new_start_y:new_end_y, new_start_x:new_end_x];
                # cv2.imwrite("teste1.png",imagem); #exit();                
                # cv2.imshow("teste1",imagem)
               

                img_h, img_w = imagem.shape[:2];
                if data_i >= 1 or amplie:
                    if (width ) < 0.7:
                        factor = 12;
                new_w = int(img_w * factor)
                new_h = int(img_h * factor)

                
                if new_w <= 1 or new_h <= 1:
                    message = f"Error, check the video; it seems probably there is no droplet image starting from {int(time)} s."
                    show_message(self, "Check the video", message, details=None, level="error")
                    # print(f"Error, check the video; it seems probably there is no droplet image starting from {int(time)} s.")                   
                    return None
                
                
                
                imagem = cv2.resize(imagem, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                # cv2.imwrite("saida_crop.png",imagem);

                # start morphological analysis of image               
                

                # Convert the image to grayscale
                imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
                
                
                
                # edges = cv2.Canny(imagem_cinza, 100, 200)
                

                imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (7, 7), 0);
                #cv2.imshow("image suavizada", imagem_suavizada)
                # cv2.imwrite("saida_suv.png",imagem_suavizada);
                

                # Apply thresholding to segment the figure
                ret, imagem_binaria = cv2.threshold(imagem_suavizada, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU);
                
                # file_img = os.path.join(path_dir_imgs,self.name_file+'_img_'+str(data_i) + '_Bin_.jpg');
                # cv2.imwrite("saida_bin.png",imagem_binaria);
                #imagem_binaria = cv2.adaptiveThreshold(imagem_cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 13, 4)
                #cv2.imshow("image 00", imagem_binaria)



                # Apply morphological operations to remove noise
                kernel = numpy.ones((3, 3), numpy.uint8)                
#                 imagem_binaria1 = cv2.morphologyEx(imagem_binaria, cv2.MORPH_ERODE, kernel, iterations=2)                
#                 #Removes pixels from the edges of the object. It works as a kind of "shrinking" of the image.               
#                 #Useful for removing small noises and highlighting smaller structures.
#                 
#                 imagem_binaria2= cv2.morphologyEx(imagem_binaria, cv2.MORPH_DILATE, kernel, iterations=2)                
#                 # Removes small noises. Useful for filling small holes and connecting disconnected components.
#                 
#                 imagem_binaria3 = cv2.morphologyEx(imagem_binaria, cv2.MORPH_OPEN, kernel, iterations=40)                
#                 #Closes small holes inside objects.
#                 
#                 imagem_binaria4 = cv2.morphologyEx(imagem_binaria, cv2.MORPH_CLOSE, kernel, iterations=30)                
#                 #Closes small holes inside objects.
#                 
                imagem_binaria5 = cv2.morphologyEx(imagem_suavizada, cv2.MORPH_GRADIENT, kernel, iterations=2)                
#                 #Highlights the edges of objects. Useful for highlighting the edges of objects.
#                 
#                 imagem_binaria6 = cv2.morphologyEx(imagem_binaria, cv2.MORPH_TOPHAT, kernel, iterations=10)                
#                 # Highlights small protrusions. Useful for highlighting small protrusions or irregularities on the object.
#                 
#                 imagem_binaria7 = cv2.morphologyEx(imagem_binaria, cv2.MORPH_BLACKHAT, kernel, iterations=2)
                #Highlights small depressions. Useful for highlighting small depressions or holes in the object.



                # ret, imagem_binaria = cv2.threshold(imagem_binaria4, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU);
                # imagem_binaria2 = cv2.morphologyEx(imagem_binaria2, cv2.MORPH_ERODE, kernel, iterations=3)


                
                # cv2.imshow("image_suv", imagem_suavizada)
                # cv2.imshow("image 0", imagem_binaria)
                # cv2.imshow("image 1", imagem_binaria1)
                # cv2.imshow("image 2", imagem_binaria2)
                # cv2.imshow("image 3", imagem_binaria3)
                # cv2.imshow("image 4", imagem_binaria4)
                # cv2.imshow("image 5", imagem_binaria5)
                # cv2.imshow("image 6", imagem_binaria6)
                # cv2.imshow("image 7", imagem_binaria7)
                
               


                # Applying adaptive binarization
                #imagem_binaria = cv2.adaptiveThreshold(
                    #imagem_binaria,                        # Imagem em escala de cinza
                    #125,                           # Valor máximo a ser atribuído aos pixels acima do limiar
                    #cv2.ADAPTIVE_THRESH_MEAN_C, # Método de limiar adaptativo
                    #cv2.THRESH_BINARY,             # Tipo de limiar
                    #5,                            # Tamanho do bloco de pixels (deve ser um número ímpar)
                    #20                              # Constante subtraída da média ou mediana
                #)

                #ret, imagem_binaria = cv2.threshold(imagem_binaria, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU);


                imagem_binaria = imagem_binaria5
                edges = cv2.Canny(imagem_binaria, 50, 150)
                # cv2.imshow("imagem_binaria", imagem_binaria)
                # cv2.imwrite("saida_bin5.png",imagem_binaria);


                # Find contours in binary image
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE);

                text_position = (50, 50)
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale_font = 1
                text_color = (125, 125, 125)  # White
                line_thickness = 2

                if contours:
                    
                    pontos = numpy.vstack(contours).squeeze() # Combine all contour points into a single list
                    x_start, y_start, width, height = cv2.boundingRect(pontos)  #Find the bounding rectangle that groups all contours
                    imagem_temp = imagem.copy()     
                    cv2.rectangle(imagem, (x_start, y_start), (x_start + width, y_start + height), (0, 255, 0), 2)
                    width = int( width / factor ) 
                    height = int( height / factor) 
                    temp_size_window[data_i][0] = width 
                    temp_size_window[data_i][1] = height
                       
                    
                    #save data 
                    data_time_size[data_i][0] = time; # time
                    data_time_size[data_i][1] = (width / 2.) / (self.px_mm ); # width -> semi axes 
                    data_time_size[data_i][2] = (height/ 2.) / (self.px_mm); # height -> semi axes 
                   
                    if data_i == 0: 
                        self.Vo = calcule_vol_spheroide(data_time_size[data_i][1], data_time_size[data_i][2] ) / 1000. # use in mL
                    temp = datetime.fromtimestamp(self.video_m) + timedelta(seconds=time);
                    data_time_size[data_i][3] = temp.timestamp()
                    data_time_size[data_i][4] = data_time_size[data_i][0] / 60.
                    data_time_size[data_i][5] = frame_count;
                    data_time_size[data_i][6] = calcule_surface_spheroide( data_time_size[data_i][2], data_time_size[data_i][1]); # calcule area
                    data_time_size[data_i][7] = calcule_concentration( data_time_size[data_i][2], data_time_size[data_i][1], self.Co, self.Vo)  / self.Co # calcule concentration
                    data_time_size[data_i][8] = calcule_vol_spheroide(data_time_size[data_i][2], data_time_size[data_i][1]) 
                    
                    file_img = os.path.join(path_dir_imgs,self.name_file+'_img_'+str(data_i) + '.jpg');
                    file_data_imgs.write(file_img+" "+"{:7.3f}".format(time)+" s "+"{:8.4e}".format(data_time_size[data_i][6])+" mg/ml \n");
                    if self.print_pdf:
                        cv2.putText(imagem,str(time), text_position, font, scale_font, text_color, line_thickness, cv2.LINE_AA)
                        cv2.imwrite(file_img,imagem);
                    # cv2.imwrite("saida_edge.png",imagem);
                    # print(temp_m[flag_temp,0] , data_time_size[data_i][1] , temp_m[flag_temp,0] - data_time_size[data_i][1] )
                    # if temp_m[flag_temp,1] > 0. and abs(temp_m[flag_temp,0] - data_time_size[data_i][1] ) < 0.01:
                    #     # print('>>>>>', data_time_size[data_i][1], data_time_size[data_i][2] )
                    #     str_valor = f"{data_time_size[data_i][1]:.2f}"
                    #     str_valor2 = f"{data_time_size[data_i][2]:.2f}"
                    #     file_img = os.path.join(path_dir_imgs,self.name_file+'_img_'+str(data_i)+'_'+str_valor+'_' + str_valor2+ '_.jpg');
                    #     cv2.imwrite(file_img,imagem_temp);
                    #     temp_m[flag_temp,1] = temp_m[flag_temp,1] - 1
                        # if temp_m[flag_temp,1] < 1: flag_temp = flag_temp + 1;
                        
                    

                data_i = data_i +1;
                # cv2.imshow("image fim", imagem)
                # input("Press enter to continue")

            frame_count += 1
            elapsed_time = timelib.time() - start_time;

            # print(f"Iteration {frame_count + 1}/{(self.time_limit*fps)}, Elapsed time: {elapsed_time:.2f} seconds", end='\r')
            progress.update(frame_count, elapsed_time)          
            if progress.was_canceled():
                progress.finish()
                # print("Process canceled by user.")
                return None
            
            has_frame, frame = video.read()

        progress.finish()
        file_data_imgs.close();
        
        
        new_data_time_size = delete_value_extrem(data_time_size);
        
        self.coef_pol_w = numpy.polyfit(new_data_time_size[:, 0],new_data_time_size[:, 1],12);
        self.coef_pol_h = numpy.polyfit(new_data_time_size[:, 0],new_data_time_size[:, 2],12);
        self.coef_pol_area = numpy.polyfit(new_data_time_size[:, 0],new_data_time_size[:, 6],12);
        self.coef_pol_conc = numpy.polyfit(new_data_time_size[:, 0],new_data_time_size[:, 7],12);
  
        



        file_out = os.path.join(path_dir_imgs,self.name_file+'_Video_time_size.csv');
        file_out = os.path.normpath(file_out);
        save_data_video(new_data_time_size,self.coef_pol_w, self.coef_pol_h, self.coef_pol_area, self.coef_pol_conc, file_out);
        


        file_out = os.path.join(path_dir_imgs,self.name_file+'_sizes.png');
        file_out = os.path.normpath(file_out);
        plot_data(new_data_time_size[:, 0],new_data_time_size[:, 1], new_data_time_size[:, 2],  new_data_time_size[:, 6], new_data_time_size[:,7], new_data_time_size[:,8], self.coef_pol_w, self.coef_pol_h, self.coef_pol_area, self.coef_pol_conc, file_out);


        video.release();
        cv_destroy_all_windows_safe();
        
        # print("")

        if self.print_pdf:
            self.print_frames_pdf(path_dir_imgs, file_image_str)
        

        return file_out



class ProgressHandler:

    def __init__(self, parent=None, label="Processing...", maximum=100):
        
        self.parent = parent
        self.maximum = maximum
        self.current = 0
        self.use_gui = False
        self.progress = None

        # Detecta se GUI está ativa
        app = QApplication.instance()
        if app is not None:
            try:
                # Tenta criar mesmo sem parent QWidget
                if isinstance(parent, QWidget):
                    self.progress = QProgressDialog(label, "Cancel", 0, maximum, parent)
                else:
                    self.progress = QProgressDialog(label, "Cancel", 0, maximum)
                self.progress.setWindowTitle("Please wait")
                self.progress.setWindowModality(Qt.WindowModal)
                self.progress.setMinimumDuration(0)
                self.progress.setValue(0)
                self.use_gui = True
            except Exception as e:
                print(f"[ProgressHandler] ⚠️ Falling back to terminal mode: {e}")
                self.use_gui = False
        else:
            self.use_gui = False

    def update(self, value, elapsed=None):
        """Atualiza o progresso (GUI ou terminal)"""
        self.current = value
        if self.use_gui and self.progress:
            self.progress.setValue(value)
            QApplication.processEvents()
        else:
            if elapsed is not None:
                print(
                    f"Iteration {value}/{self.maximum}, Elapsed time: {elapsed:.2f} seconds",
                    end="\r"
                )
            else:
                print(f"Progress: {value}/{self.maximum}", end="\r")

    def was_canceled(self):
        """Verifica se o usuário cancelou (apenas GUI)"""
        if self.use_gui and self.progress:
            return self.progress.wasCanceled()
        return False

    def finish(self):
        """Finaliza o progresso"""
        if self.use_gui and self.progress:
            self.progress.setValue(self.maximum)
            QApplication.processEvents()  # 🔹 força atualização final
            self.progress.close()         # 🔹 fecha explicitamente o diálogo
            QApplication.processEvents()  # 🔹 garante que o fechamento seja processado
        else:
            print()




def menu():
    print("\n Options:")
    print("1. Video analysis")
    print("2. Frame analysis")
    print("3. Join frames and videos")
    print("4. Create data treatment list")
    print("5. Exit");




def save_data_video(data_in, coef_w, coef_h, coef_area, coef_conc, output_file):


    file_op = open(output_file, "w", encoding='utf-8');

    file_op.write(f"Coeficient width:  {', '.join([f'{i_coef:.7e}' for i_coef in coef_w])}\n")
    file_op.write(f"Coeficient height:  {', '.join([f'{i_coef:.7e}' for i_coef in coef_h])}\n")
    file_op.write(f"Coeficient area: {', '.join([f'{i_coef:.7e}' for i_coef in coef_area])}\n")
    file_op.write(f"Coeficient concentration: {', '.join([f'{i_coef:.7e}' for i_coef in coef_conc])}\n")
    file_op.write("Frame,dropDX(mm),dropDY(mm),surface(mm^2),Volume(\u03bcL),RelativeConcentration(%),date,time(s),time(min)\n")


    for i_data in range(0, len(data_in)):
        
        
        str_ = f"{int(data_in[i_data,4]):>5d}, {data_in[i_data,1]:.3e}, {data_in[i_data,2]:.3e},  {data_in[i_data,6]:.3e}, {data_in[i_data,8]:.3e}, {data_in[i_data,7]:.3e}, {datetime.fromtimestamp(data_in[i_data,3]).strftime('%Y-%m-%d %H:%M:%S')}, {data_in[i_data,0]:.2f}, {data_in[i_data,4]:.2f} \n";

        file_op.write(str_);
    file_op.close()

def save_data_edf(data_in, output_file, option):


    format_time = '%Y-%m-%d %H:%M:%S'

    file_op = open(output_file, "w", encoding='utf-8');

    if option == 0: file_op.write("Frame, dropDX(mm), dropDY(mm), surface(mm^2), RelativeConcentration(%), date, time(s)\n")
    else: file_op.write("Frame, date, time(s) \n")

    for i_data in data_in:

        if option == 0:
            str_ = f"{i_data['file']}, {float(i_data['dropDX']):.8e}, {float(i_data['dropDY']):.8e}, {float(i_data['area']):.8e}, {float(i_data['concentration']):.8e}, {i_data['date']}, {float(i_data['start_time']):.2f} \n";

        else:
            str_ = f"{i_data['file']}, {i_data['date']}, {float(i_data['start_time']):.2f} \n";
        file_op.write(str_);
    file_op.close()
    
    
def show_message(self, title, message, details=None, level="error"):

    import traceback
    import sys
    from PyQt5.QtWidgets import QMessageBox, QApplication

    app = QApplication.instance()  # verifica se a GUI está ativa

    if app is not None:

        msg = QMessageBox(self if hasattr(self, "windowTitle") else None)
        if level.lower() == "error":
            msg.setIcon(QMessageBox.Critical)
        elif level.lower() == "warning":
            msg.setIcon(QMessageBox.Warning)
        else:
            msg.setIcon(QMessageBox.Information)

        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.exec_()
    else:

        print(f"\n{'='*60}")
        print(f"[{level.upper()}] {title}")
        print(f"→ {message}")
        if details:
            print("-" * 60)
            print(details)
            print("-" * 60)
        print(f"{'='*60}\n")


def read_file_video(input_file):

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        temp = lines[0].strip();
        coef_w_values = temp[len("Coeficient width:"):].split(',')
        coef_w = [float(value.strip()) for value in coef_w_values]
        temp = lines[1].strip();
        coef_h_values = temp[len("Coeficient height:"):].split(',')
        coef_h = [float(value.strip()) for value in coef_h_values]
        temp = lines[2].strip();
        coef_area_values = temp[len("Coeficient area:"):].split(',')
        coef_area = [float(value.strip()) for value in coef_area_values]
        temp = lines[3].strip();
        coef_pol_conc_values = temp[len("Coeficient concentration:"):].split(',')
        coef_conc = [float(value.strip()) for value in coef_pol_conc_values]
        



    # Reading data
    data = []
    for line in lines[5:]:
        frame, dropDX, dropDY, area, volume, concentration, date_str, time_s, time_min = line.split(', ');
        date_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        data.append({
            'Frame': int(frame),
            'dropDX(mm)': float(dropDX), 
            'dropDY(mm)': float(dropDY), 
            'area(mm^2)': float(area), 
            'concentration(mg/ml)': float(concentration), 
            'date': date_time, 
            'time(s)': float(time_s.strip())
        } )


    return coef_w, coef_h, coef_area, coef_conc, data


def calcule_surface_spheroide(edge_1, edge_2):
    
    if np.isclose(edge_1, edge_2):  # sphere
        
        return 4. * np.pi * edge_1**2     
     
    # oblate spheroide: edge_1 > edge_2
    if edge_1 > edge_2:
        e = np.sqrt(1.0 - (edge_2*edge_2)/(edge_1*edge_1))           # 0 < e < 1
        # atanh(e) = 0.5 * ln((1+e)/(1-e))
        atanh_e = 0.5 * np.log((1.0 + e)/(1.0 - e))
        return 2.0 * np.pi * edge_1*edge_1 * (1.0 + ((1.0 - e*e)/e) * atanh_e)    
    else: # prolate spheroide: edge_2 > edge_1 
        e = np.sqrt(1.0 - (edge_1*edge_1)/(edge_2*edge_2))           # 0 < e < 1
        return 2.0 * np.pi * edge_1*edge_1 * (1.0 + (edge_2/(edge_1*e)) * np.arcsin(e))
    


def _int_to_fourcc(v: int) -> str:
    if not v:
        return ""
    chars = []
    for i in range(4):
        chars.append(chr((v >> (8 * i)) & 0xFF))
    s = "".join(chars)
    if not s.isprintable():
        return ""
    return s


def _default_fourcc_candidates_for_ext(ext: str) -> List[str]:
    ext = ext.lower()
    # Reasonable candidates given typical OpenCV/FFmpeg builds (no guarantee)
    if ext in (".mp4", ".m4v", ".mov"):
        return ["mp4v", "avc1", "h264"]  # mp4v is most portable in OpenCV wheels
    if ext == ".avi":
        return ["MJPG", "XVID", "mp4v"]
    if ext == ".mkv":
        return ["mp4v", "MJPG", "XVID"]
    # Very uncommon/unsupported for writing via OpenCV:
    if ext == ".flv":
        return []  # force user to change container
    return ["mp4v"]


def _pick_writer_fourcc(cap: cv2.VideoCapture, out_path: str, user_codec: Optional[str]) -> List[str]:
    ext = os.path.splitext(out_path)[1].lower()
    # If user forces a codec, try it first
    candidates: List[str] = []
    if user_codec:
        candidates.append(user_codec)

    # Try to reuse detected codec (rarely usable for writing, but try)
    detected = _int_to_fourcc(int(cap.get(cv2.CAP_PROP_FOURCC)))
    if detected and detected.strip("\x00").strip():
        candidates.append(detected)

    # Add common candidates for the chosen extension
    candidates += _default_fourcc_candidates_for_ext(ext)

    # Finally, add a few generic fallbacks
    for fallback in ("mp4v", "MJPG", "XVID", "avc1"):
        if fallback not in candidates:
            candidates.append(fallback)

    # Remove empties/dupes while preserving order
    seen = set()
    out = []
    for c in candidates:
        c = (c or "").strip()
        if not c:
            continue
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def parse_drop_spec(spec: str, total_frames: int) -> Set[int]:
    if not spec:
        return set()
    result: Set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            a = a.strip()
            b = b.strip()
            if not a.isdigit() or not b.isdigit():
                raise ValueError(f"Invalid range '{chunk}' in --drop spec")
            start = int(a)
            end = int(b)
            if start > end:
                start, end = end, start
            for i in range(start, end + 1):
                if 0 <= i < total_frames:
                    result.add(i)
        else:
            if not chunk.isdigit():
                raise ValueError(f"Invalid index '{chunk}' in --drop spec")
            i = int(chunk)
            if 0 <= i < total_frames:
                result.add(i)
    return result

def _open_writer_any(tmp_out_path: str, fps: float, size: Tuple[int, int], candidates: List[str]) -> Tuple[Optional[cv2.VideoWriter], Optional[str]]:
    

    for c in candidates:
        try:
            fourcc = cv2.VideoWriter_fourcc(*c)
            w = cv2.VideoWriter(tmp_out_path, fourcc, fps, size)
            if w.isOpened():
                return w, c
            # release and try next
            w.release()
        except Exception:
            pass
    return None, None