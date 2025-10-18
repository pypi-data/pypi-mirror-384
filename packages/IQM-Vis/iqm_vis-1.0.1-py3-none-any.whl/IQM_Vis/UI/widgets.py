'''
UI create widgets
'''
# Author: Matt Clifford <matt.clifford@bristol.ac.uk>
# License: BSD 3-Clause License

import re
import os
from functools import partial
import datetime

import numpy as np
from PyQt6.QtWidgets import QPushButton, QLabel, QSlider, QCheckBox, QComboBox, QLineEdit
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QValidator
from PyQt6.QtCore import Qt, pyqtSlot, QLocale

import IQM_Vis
from IQM_Vis.UI.custom_widgets import ClickLabel
from IQM_Vis.utils import gui_utils, plot_utils, image_utils, save_utils

# sub class used by IQM_Vis.main.make_app to initialise widgets and general UI functions for widgets
class widgets():
    def init_widgets(self, **kwargs):
        '''
        create all the widgets we need and init params
        '''
        self._init_widgets()
        self.set_image_name_text()
        self._init_image_settings()

    def _init_widgets(self):
        '''
        create all the widgets we need and init params
        '''
        self.export_in_progress = False
        self.last_export = None
        self.tool_tip_style = """QToolTip {background-color: black; color: white; border: black solid 1px}"""
        # first setup the slider data
        self.sliders = {'transforms': {}, 'metric_params': {}}
        self._init_sliders(self.sliders['transforms'], self.checked_transformations,  param_group='transforms')
        self._init_sliders(self.sliders['metric_params'], self.metric_params, param_group='metric_params')

        self.widget_row = {}
        for i, data_store in enumerate(self.data_stores):   # create each row of the widgets
            self.widget_row[i] = {'images':{}, 'metrics':{}, 'metric_images':{}}
            '''image and transformed image'''
            for image_name in ['original', 'transformed']:
                self.widget_row[i]['images'][image_name] = {}
                # image widget
                self.widget_row[i]['images'][image_name]['data'] = QLabel(self)
                self.widget_row[i]['images'][image_name]['data'].setAlignment(Qt.AlignmentFlag.AlignCenter)
                # image label
                self.widget_row[i]['images'][image_name]['label'] = QLabel(self)
                self.widget_row[i]['images'][image_name]['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.widget_row[i]['images'][image_name]['label'].setText(image_name)

            '''metric images'''
            for metric_image in data_store.metric_images:
                if metric_image in self.checked_metric_images:
                    self.widget_row[i]['metric_images'][metric_image] = {}
                    self.widget_row[i]['metric_images'][metric_image]['data'] = QLabel(self)
                    self.widget_row[i]['metric_images'][metric_image]['data'].setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # image label
                    self.widget_row[i]['metric_images'][metric_image]['label'] = QLabel(self)
                    self.widget_row[i]['metric_images'][metric_image]['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)

            '''metrics graphs'''
            im_pair_name = gui_utils.get_image_pair_name(data_store)
            self.widget_row[i]['metrics']['info'] = {}
            self.widget_row[i]['metrics']['info']['label'] = QLabel(self)
            self.widget_row[i]['metrics']['info']['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.widget_row[i]['metrics']['info']['label'].setText('Metrics '+im_pair_name)
            if self.metrics_info_format == 'graph':
                self.widget_row[i]['metrics']['info']['data'] = gui_utils.MplCanvas(size=(self.graph_size/10, self.graph_size/10))
            else:
                self.widget_row[i]['metrics']['info']['data'] = QLabel(self)
                self.widget_row[i]['metrics']['info']['data'].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.widget_row[i]['metrics']['info']['data'].setText('')
            # metrics average graphs
            if self.metrics_avg_graph:
                self.widget_row[i]['metrics']['avg'] = {}
                self.widget_row[i]['metrics']['avg']['label'] = QLabel(self)
                self.widget_row[i]['metrics']['avg']['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.widget_row[i]['metrics']['avg']['label'].setText('IQM Averages')
                self.widget_row[i]['metrics']['avg']['data'] = gui_utils.MplCanvas(size=(self.graph_size/10, self.graph_size/10), polar=True)
                self.widget_row[i]['metrics']['avg']['data'].setToolTip('Mean metric value over the range of each transform.')
                self.widget_row[i]['metrics']['avg']['data'].setStyleSheet(self.tool_tip_style)
                self.widget_row[i]['metrics']['avg']['save_button'] = QPushButton('Adjust or Save', self)
                self.widget_row[i]['metrics']['avg']['save_button'].clicked.connect(partial(self.plot_radar_mlp, i))
            if self.metric_range_graph:
                self.widget_row[i]['metrics']['range'] = {}
                self.widget_row[i]['metrics']['range']['label'] = QLabel(self)
                self.widget_row[i]['metrics']['range']['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.widget_row[i]['metrics']['range']['label'].setText('Response Profiles')
                self.widget_row[i]['metrics']['range']['data'] = gui_utils.MplCanvas(size=(self.graph_size/10, self.graph_size/10))
                self.widget_row[i]['metrics']['range']['data'].setToolTip('Single transformation value range for all metrics.')
                self.widget_row[i]['metrics']['range']['data'].setStyleSheet(self.tool_tip_style)
                self.widget_row[i]['metrics']['range']['save_button'] = QPushButton('Adjust or Save', self)
                self.widget_row[i]['metrics']['range']['save_button'].clicked.connect(partial(self.plot_metric_range_mlp, i))
            # correlation graphs
            self.widget_row[i]['metrics']['correlation'] = {}
            self.widget_row[i]['metrics']['correlation']['label'] = QLabel(self)
            self.widget_row[i]['metrics']['correlation']['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.widget_row[i]['metrics']['correlation']['label'].setText('Human Correlation')
            self.widget_row[i]['metrics']['correlation']['data'] = gui_utils.MplCanvas(size=(self.graph_size/10, self.graph_size/10))
            self.widget_row[i]['metrics']['correlation']['data'].setToolTip('Human scores versus IQMs.\nMean shown with points\nStandard deviation shown with bars.\nClick points to show image.')
            self.widget_row[i]['metrics']['correlation']['data'].setStyleSheet(self.tool_tip_style)
            # JND graphs
            self.widget_row[i]['metrics']['JND'] = {}
            self.widget_row[i]['metrics']['JND']['label'] = QLabel(self)
            self.widget_row[i]['metrics']['JND']['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.widget_row[i]['metrics']['JND']['label'].setText('Just Noticeable Difference')
            self.widget_row[i]['metrics']['JND']['data'] = gui_utils.MplCanvas(size=(self.graph_size/10, self.graph_size/10))
            self.widget_row[i]['metrics']['JND']['data'].setToolTip(
                'Just Noticeable Difference shows the perceivable effect of a distortion for a human subject.')
            self.widget_row[i]['metrics']['JND']['data'].setStyleSheet(self.tool_tip_style)


        '''buttons'''
        self.widget_controls = {'button': {}, 'slider': {}, 'label': {}, 'check_box': {}, 'images': {}}
        
        if (self.metrics_avg_graph or self.metric_range_graph):
            # Update graphs
            self.widget_controls['button']['force_update'] = QPushButton('Update Graphs', self)
            self.widget_controls['button']['force_update'].setToolTip('Update graphs using all the current slider values.')
            self.widget_controls['button']['force_update'].setStyleSheet(self.tool_tip_style)
            self.widget_controls['button']['force_update'].clicked.connect(self.display_images)
            self.widget_controls['button']['force_update'].clicked.connect(partial(self.redo_plots, True))
            # Change plot limits
            self.widget_controls['check_box']['graph_limits'] = QCheckBox('Squeeze plots')
            self.widget_controls['check_box']['graph_limits'].setToolTip('Set the scale of the plots to the metric data range.')
            self.widget_controls['check_box']['graph_limits'].setStyleSheet(self.tool_tip_style)
            self.widget_controls['check_box']['graph_limits'].setCheckState(Qt.CheckState.Unchecked)
            self.widget_controls['check_box']['graph_limits'].stateChanged.connect(self.change_plot_lims)

        if self.metric_range_graph:
            # buttons to control which metric range graph to show
            self.widget_controls['button']['next_metric_graph'] = QPushButton('->', self)
            self.widget_controls['button']['next_metric_graph'].clicked.connect(partial(self.change_metric_range_graph, 1))
            self.widget_controls['button']['prev_metric_graph'] = QPushButton('<-', self)
            self.widget_controls['button']['prev_metric_graph'].clicked.connect(partial(self.change_metric_range_graph, -1))
        # buttons to control which correlation graph to show
        self.widget_controls['button']['next_correlation_graph'] = QPushButton('->', self)
        self.widget_controls['button']['next_correlation_graph'].clicked.connect(partial(self.change_metric_correlations_graph, 1))
        self.widget_controls['button']['prev_correlation_graph'] = QPushButton('<-', self)
        self.widget_controls['button']['prev_correlation_graph'].clicked.connect(partial(self.change_metric_correlations_graph, -1))

        if self.dataset:
            # control what image is used from the dataset
            self.widget_controls['button']['next_data'] = QPushButton('->', self)
            self.widget_controls['button']['next_data'].clicked.connect(partial(self.change_preview_images, 1))
            self.widget_controls['button']['prev_data'] = QPushButton('<-', self)
            self.widget_controls['button']['prev_data'].clicked.connect(partial(self.change_preview_images, -1))
            self.widget_controls['label']['data'] = QLabel(self)
            self.widget_controls['label']['data'].setText('Change Image:')
            self.widget_controls['label']['data_num'] = QLabel(self)
            self.widget_controls['label']['data_num'].setText('1/1')
            self.widget_im_num_hash = {}
            for im in range(self.num_images_scroll_show):
                self.widget_controls['images'][im] = QLabel( self)
                self.widget_controls['images'][im].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.widget_controls['images'][im].mousePressEvent = partial(self.change_data_click_im, im)
                self.widget_im_num_hash[im] = im # store the ind number of each im widget preview

        # launch experiment buttons
        self.widget_controls['button']['launch_exp_2AFC'] = QPushButton('Run 2AFC Experiment', self)
        self.widget_controls['button']['launch_exp_2AFC'].setToolTip('Two Alternative Forced Choice Experiment')
        self.widget_controls['button']['launch_exp_2AFC'].clicked.connect(self.launch_experiment_2AFC)
        self.widget_controls['button']['launch_exp_JND'] = QPushButton('Run JND Experiment', self)
        self.widget_controls['button']['launch_exp_JND'].setToolTip('Just Noticeable Difference Experiment')
        self.widget_controls['button']['launch_exp_JND'].clicked.connect(self.launch_experiment_JND)
        # load 2AFC experiment button
        self.widget_controls['button']['load_exp'] = QPushButton('Load Experiment', self)
        self.widget_controls['button']['load_exp'].clicked.connect(self.load_experiment_from_dir)
        # load JNDexperiment button
        self.widget_controls['button']['load_exp_JND'] = QPushButton('Load Experiment', self)
        self.widget_controls['button']['load_exp_JND'].clicked.connect(self.load_experiment_from_dir_JND)
        # export images button
        self.widget_controls['button']['export_images'] = QPushButton('Export Images', self)
        self.widget_controls['button']['export_images'].clicked.connect(self.export_trans_images)
        


        '''sliders'''
        self.params_from_sliders = {}
        for param_group, slider_group in self.sliders.items():
            self.params_from_sliders[param_group] = {}
            self.widget_controls['button'][param_group] = {}
            self.widget_controls['button'][param_group]['reset_sliders'] = QPushButton('Reset', self)
            if param_group == 'metric_params':
                redo_graphs = True
            else:
                redo_graphs = False
            self.widget_controls['button'][param_group]['reset_sliders'].clicked.connect(
                partial(self.reset_slider_group, param_group, redo_graphs))

            for key, item_sliders in slider_group.items():
                self.widget_controls['slider'][key] = {}
                self.widget_controls['slider'][key]['data'] = QSlider(Qt.Orientation.Horizontal)
                self.widget_controls['slider'][key]['data'].setMinimum(0)
                self.widget_controls['slider'][key]['data'].setMaximum(len(item_sliders['values'])-1)
                for func in item_sliders['value_change']:
                    self.widget_controls['slider'][key]['data'].valueChanged.connect(func)
                for func in item_sliders['release']:
                    self.widget_controls['slider'][key]['data'].sliderReleased.connect(func)
                self.params_from_sliders['transforms'][key] = item_sliders['init_ind']
                self.widget_controls['slider'][key]['label'] = QLabel(self)
                self.widget_controls['slider'][key]['label'].setAlignment(Qt.AlignmentFlag.AlignRight)
                self.widget_controls['slider'][key]['label'].setText(f"{key}:")
                self.widget_controls['slider'][key]['value'] = QLabel(self)
                self.widget_controls['slider'][key]['value'].setAlignment(Qt.AlignmentFlag.AlignLeft)
                self.widget_controls['slider'][key]['value'].setText(str(self.params_from_sliders['transforms'][key]))

        ''' experiment options '''
        self.widget_experiment_params = {}
        
        for trans_name, deets in self.checked_transformations.items():
            self.widget_experiment_params[trans_name] = {}
            self.widget_experiment_params[trans_name]['check_box'] = QCheckBox(self)
            self.widget_experiment_params[trans_name]['check_box'].setChecked(True)
            self.widget_experiment_params[trans_name]['check_box'].stateChanged.connect(partial(self.change_text_exp_trans, 
                                                                                                  trans=trans_name))

            self.widget_experiment_params[trans_name]['name'] = QLabel(self)
            self.widget_experiment_params[trans_name]['name'].setText(trans_name)

            self.widget_experiment_params[trans_name]['min'] = QLabel(self)
            self.widget_experiment_params[trans_name]['min'].setText('min:')
            self.widget_experiment_params[trans_name]['min_edit'] = QLineEdit()
            self.widget_experiment_params[trans_name]['min_edit'].setValidator(get_float_validator())
            self.widget_experiment_params[trans_name]['min_edit'].textChanged.connect(partial(self.colour_lineedit, self.widget_experiment_params[trans_name]['min_edit']))
            self.widget_experiment_params[trans_name]['min_edit'].setText(f"{deets['min']}")

            self.widget_experiment_params[trans_name]['max'] = QLabel(self)
            self.widget_experiment_params[trans_name]['max'].setText('max:')
            self.widget_experiment_params[trans_name]['max_edit'] = QLineEdit()
            self.widget_experiment_params[trans_name]['max_edit'].setValidator(get_float_validator())
            self.widget_experiment_params[trans_name]['max_edit'].textChanged.connect(partial(self.colour_lineedit, self.widget_experiment_params[trans_name]['max_edit']))
            self.widget_experiment_params[trans_name]['max_edit'].setText(f"{deets['max']}")

            self.widget_experiment_params[trans_name]['steps'] = QLabel(self)
            self.widget_experiment_params[trans_name]['steps'].setText('steps:')
            self.widget_experiment_params[trans_name]['steps_edit'] = QLineEdit()
            self.widget_experiment_params[trans_name]['steps_edit'].setValidator(QIntValidator())
            self.widget_experiment_params[trans_name]['steps_edit'].setMaxLength(2)
            self.widget_experiment_params[trans_name]['steps_edit'].setText(f"{self.num_step_experiment}")
        # change save folder button
        self.widget_controls['label']['exp_change_save'] = QLabel(self)
        self.widget_controls['label']['exp_change_save'].setText(f'Root Save Folder: {self.default_save_dir}')
        self.widget_controls['button']['exp_change_save'] = QPushButton('Change', self)
        self.widget_controls['button']['exp_change_save'].clicked.connect(self.change_save_folder)
        # dataset name
        self.widget_controls['label']['exp_change_dataset_name'] = QLabel(self)
        self.widget_controls['label']['exp_change_dataset_name'].setText(f'Dataset Name (JND)')
        self.widget_controls['button']['exp_change_dataset_name'] = QLineEdit(self)
        self.widget_controls['button']['exp_change_dataset_name'].setText(
            self.default_dataset_name)
        self.widget_controls['button']['exp_change_dataset_name'].textChanged.connect(
            self.change_dataset_name)
        self.widget_controls['label']['exp_im_nums'] = QLabel(self)
        self.widget_controls['label']['exp_im_nums'].setText('Dataset Range (JND):')
        self.widget_controls['label']['exp_im_nums_dash'] = QLabel(self)
        self.widget_controls['label']['exp_im_nums_dash'].setText('-')
        self.widget_controls['label']['range_edit_lower'] = QLineEdit()
        self.widget_controls['label']['range_edit_lower'].setValidator(QIntValidator())
        self.exp_range_lower = 1
        self.widget_controls['label']['range_edit_lower'].setText(
            f"{self.exp_range_lower}")
        self.widget_controls['label']['range_edit_lower'].textChanged.connect(self.JND_dataset_range_lower)
        self.widget_controls['label']['range_edit_upper'] = QLineEdit()
        self.widget_controls['label']['range_edit_upper'].setValidator(QIntValidator())
        self.exp_range_upper = len(self.data_stores[0])
        self.widget_controls['label']['range_edit_upper'].setText(
            f"{self.exp_range_upper}")
        self.widget_controls['label']['range_edit_upper'].textChanged.connect(self.JND_dataset_range_upper)

        ''' export options '''
        self.widget_export = {}
        
        for trans_name, deets in self.checked_transformations.items():
            self.widget_export[trans_name] = {}
            self.widget_export[trans_name]['check_box'] = QCheckBox(self)
            self.widget_export[trans_name]['check_box'].setChecked(True)
            self.widget_export[trans_name]['check_box'].stateChanged.connect(partial(self.change_text_export_trans,
                                                                                                  trans=trans_name))

            self.widget_export[trans_name]['name'] = QLabel(self)
            self.widget_export[trans_name]['name'].setText(trans_name)

            self.widget_export[trans_name]['min'] = QLabel(self)
            self.widget_export[trans_name]['min'].setText('min:')
            self.widget_export[trans_name]['min_edit'] = QLineEdit()
            self.widget_export[trans_name]['min_edit'].setValidator(get_float_validator())
            self.widget_export[trans_name]['min_edit'].textChanged.connect(partial(self.colour_lineedit, self.widget_export[trans_name]['min_edit']))
            self.widget_export[trans_name]['min_edit'].setText(f"{deets['min']}")

            self.widget_export[trans_name]['max'] = QLabel(self)
            self.widget_export[trans_name]['max'].setText('max:')
            self.widget_export[trans_name]['max_edit'] = QLineEdit()
            self.widget_export[trans_name]['max_edit'].setValidator(get_float_validator())
            self.widget_export[trans_name]['max_edit'].textChanged.connect(partial(self.colour_lineedit, self.widget_export[trans_name]['max_edit']))
            self.widget_export[trans_name]['max_edit'].setText(f"{deets['max']}")

            self.widget_export[trans_name]['steps'] = QLabel(self)
            self.widget_export[trans_name]['steps'].setText('steps:')
            self.widget_export[trans_name]['steps_edit'] = QLineEdit()
            self.widget_export[trans_name]['steps_edit'].setValidator(QIntValidator())
            self.widget_export[trans_name]['steps_edit'].setMaxLength(2)
            self.widget_export[trans_name]['steps_edit'].setText(f"{self.num_steps_range}")
        # change save folder button
        self.widget_controls['label']['export_change_save'] = QLabel(self)
        self.widget_controls['label']['export_change_save'].setText(f'Save Folder: {self.default_save_dir}')
        self.widget_controls['button']['export_change_save'] = QPushButton('Change', self)
        self.widget_controls['button']['export_change_save'].clicked.connect(self.change_save_folder)


    '''
    setup/helper functions
    '''
    def _init_sliders(self, sliders_dict, info_dict, param_group):
        '''
        generic initialiser of sliders (will change the dicts input rather than returning - like C++ pointers &)
            sliders_dict: holds the slider widgets
            info_dict: info to initialise the sliders
        '''
        for key, info_item in info_dict.items():
            sliders_dict[key] = {}
            sliders_dict[key]['release'] = [self.display_images]
            sliders_dict[key]['value_change'] = [partial(self.generic_value_change, key, param_group), self.display_images]
            if 'function' in info_item.keys():
                sliders_dict[key]['function'] = info_item['function']
            if 'init_value' not in info_item.keys():
                info_item['init_value'] = 0
            sliders_dict[key]['init_value_store'] = info_item['init_value']
            if 'values' in info_item.keys():
                sliders_dict[key]['values'] = info_item['values']
            else:
                if 'num_values' not in info_item.keys():
                    info_item['num_values'] = 41   # make default value for steps in slider range
                # see if we need to make odd numbers (for use with kernel sizes)
                if 'normalise' in info_item.keys():
                    # store for if min/max changed later
                    sliders_dict[key]['normalise'] = info_item['normalise']
                self.make_slider_range(sliders_dict, key, info_item['min'], info_item['max'], info_item['num_values'])
            
            # store num steps used
            sliders_dict[key]['default_num_steps'] = len(sliders_dict[key]['values'])
            # make min/max inputs
            width = 40
            sliders_dict[key]['min_edit'] = QLineEdit()
            sliders_dict[key]['min_edit'].setValidator(get_float_validator())
            sliders_dict[key]['min_edit'].textChanged.connect(partial(self.colour_lineedit, sliders_dict[key]['min_edit']))
            sliders_dict[key]['min_edit'].setText(f"{min(sliders_dict[key]['values'])}")
            sliders_dict[key]['min_edit'].setFixedWidth(width)
            sliders_dict[key]['min_edit'].editingFinished.connect(partial(self.edit_slider_vals, sliders_dict, key, info_item))
            sliders_dict[key]['min_edit'].editingFinished.connect(partial(self.generic_value_change, key, param_group))
            sliders_dict[key]['min_edit'].editingFinished.connect(self.display_images)
            sliders_dict[key]['max_edit'] = QLineEdit()
            sliders_dict[key]['max_edit'].setValidator(get_float_validator())
            sliders_dict[key]['max_edit'].textChanged.connect(partial(self.colour_lineedit, sliders_dict[key]['max_edit']))
            sliders_dict[key]['max_edit'].setText(f"{max(sliders_dict[key]['values'])}")
            sliders_dict[key]['max_edit'].setFixedWidth(width)
            sliders_dict[key]['max_edit'].editingFinished.connect(partial(self.edit_slider_vals, sliders_dict, key, info_item))
            sliders_dict[key]['max_edit'].editingFinished.connect(partial(self.generic_value_change, key, param_group))
            sliders_dict[key]['max_edit'].editingFinished.connect(self.display_images)
    
    def make_slider_range(self, sliders_dict, key, _min, _max, num_steps=None):
        if num_steps == None:
            num_steps = sliders_dict[key]['default_num_steps']
        sliders_dict[key]['values'] = np.linspace(_min, _max, num_steps)
        # see if we need to make odd numbers (for use with kernel sizes)
        if 'normalise' in sliders_dict[key].keys():
            if sliders_dict[key]['normalise'] == 'odd':
                sliders_dict[key]['values'] = np.round(sliders_dict[key]['values'])
                sliders_dict[key]['values'] = sliders_dict[key]['values'][sliders_dict[key]['values']%2 == 1]
        # get ind of the initial value to set the slider at
        sliders_dict[key]['init_ind'] = np.searchsorted(sliders_dict[key]['values'], sliders_dict[key]['init_value_store'], side='left')

    def _init_image_settings(self):
        self.widget_settings = {}

        # pre processing
        self.pre_processing_options = {'None': None,
                                       'Resize 32': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=32),
                                       'Resize 64': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=64),
                                       'Resize 128': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=128),
                                       'Resize 256': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=256),
                                       'Resize 512': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=512),
                                       'Resize 1280': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=1280),
                                       'Resize 1920': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=1920),
                                       'Resize 2560': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=2560),
                                       'Resize 3840': partial(IQM_Vis.utils.image_utils.resize_to_longest_side, side=3840),
                                       }
        if not hasattr(self, 'pre_processing_option'):
            self.pre_processing_option = 'Resize 256'  # init_val

        for i, data_store in enumerate(self.data_stores):
            if hasattr(data_store, 'image_pre_processing'):
                if str(data_store.image_pre_processing) not in [str(f) for f in self.pre_processing_options.values()]:
                    name = f"Custom {i}"
                    self.pre_processing_options[name] = data_store.image_pre_processing
                    self.pre_processing_option = name
        combobox_pre = QComboBox()
        combobox_pre.addItems(list(self.pre_processing_options.keys()))
        combobox_pre.setCurrentText(self.pre_processing_option)
        combobox_pre.activated.connect(self.enable_settings_button)
        self.widget_settings['image_pre_processing'] = {'widget': combobox_pre, 'label': QLabel('Image Pre Processing:')}
        self.change_pre_processing()   # apply default

        # post processing
        self.post_processing_options = {'None': None,
                                        'Crop Centre': partial(IQM_Vis.utils.image_utils.crop_centre, scale_factor=2, keep_size=True),
                                        'Crop Centre (No Resize)': partial(IQM_Vis.utils.image_utils.crop_centre, scale_factor=2, keep_size=False),
                                        }
        if not hasattr(self, 'post_processing_option'):
            self.post_processing_option = 'None'  # init_val
        for i, data_store in enumerate(self.data_stores):
            if hasattr(data_store, 'image_post_processing'):
                if data_store.image_post_processing not in list(self.post_processing_options.values()):
                    name = f"Custom {i}"
                    self.post_processing_options[name] = data_store.image_post_processing
                    self.post_processing_option = name
        combobox_post = QComboBox()
        combobox_post.addItems(list(self.post_processing_options.keys()))
        combobox_post.setCurrentText(self.post_processing_option)
        combobox_post.activated.connect(self.enable_settings_button)
        self.widget_settings['image_post_processing'] = {'widget': combobox_post, 'label': QLabel('Image Post Processing:')}
        self.change_post_processing()    # apply default

        # image display size
        line_edit_display = QLineEdit()
        line_edit_display.setValidator(QIntValidator())
        line_edit_display.setMaxLength(3)
        line_edit_display.setText(str(self.image_display_size))
        line_edit_display.textChanged.connect(self.enable_settings_button)
        self.widget_settings['image_display_size'] = {'widget': line_edit_display, 'label': QLabel('Image Display Size:')}

        # graph display size
        line_edit_graph = QLineEdit()
        line_edit_graph.setValidator(QIntValidator())
        line_edit_graph.setMaxLength(2)
        line_edit_graph.setText(str(self.graph_size))
        line_edit_graph.textChanged.connect(self.enable_settings_button)
        self.widget_settings['graph_display_size'] = {'widget': line_edit_graph, 'label': QLabel('Graph Display Size:')}

        # graph/experiment number of steps in the range
        line_edit_num_steps = QLineEdit()
        line_edit_num_steps.setValidator(QIntValidator())
        line_edit_num_steps.setMaxLength(4)
        line_edit_num_steps.setText(str(self.num_steps_range))
        line_edit_num_steps.textChanged.connect(self.enable_settings_button)
        self.widget_settings['graph_num_steps'] = {'widget': line_edit_num_steps, 'label': QLabel('Graph Range Step Size:')}

        # image screen calibration
        line_edit_rgb = QLineEdit()
        line_edit_rgb.setValidator(QIntValidator())
        line_edit_rgb.setMaxLength(4)
        line_edit_rgb.setText(str(self.rgb_brightness))
        line_edit_rgb.textChanged.connect(self.enable_settings_button)
        self.widget_settings['image_display_rgb_brightness'] = {
            'widget': line_edit_rgb, 'label': QLabel('RGB Max Brightness:')}

        line_edit_display = QLineEdit()
        line_edit_display.setValidator(QIntValidator())
        line_edit_display.setMaxLength(4)
        line_edit_display.setText(str(self.display_brightness))
        line_edit_display.textChanged.connect(self.enable_settings_button)
        self.widget_settings['image_display_display_brightness'] = {
            'widget': line_edit_display, 'label': QLabel('Display Max Brightness:')}

        # update settings button
        self.widget_settings['update_button'] = QPushButton('Apply Settings', self)
        # self.settings_text_colour_original = self.widget_settings['update_button'].palette().color(
        #     QPalette.ColorRole.Text).name()   # this doesn't work for some reason ...
        self.settings_text_colour_original = 'black'
        self.widget_settings['update_button'].clicked.connect(self.update_image_settings)
        self.disable_settings_button()

    '''
    ==================== functions to bind to sliders/widgets ====================
    '''
    # line edit colour based on if valid
    def colour_lineedit(self, widget, txt):
        if not is_float(txt):
            widget.setStyleSheet("color: red;")
        else:
            widget.setStyleSheet("color: black;")

    # sliders value changes
    def generic_value_change(self, key, param_group):
        index = self.widget_controls['slider'][key]['data'].value()
        self.params_from_sliders[param_group][key] = self.sliders[param_group][key]['values'][index]
        self.display_slider_num(key, param_group) # display the new value ont UI

    def edit_slider_vals(self, sliders_dict, key, info_item):
        _min = make_float_from_text(sliders_dict[key]['min_edit'].text())
        _max = make_float_from_text(sliders_dict[key]['max_edit'].text())
        self.make_slider_range(sliders_dict, key, _min, _max)
        info_item['min'] = _min
        info_item['max'] = _max

    def display_slider_num(self, key, param_group, disp_len=5):
        # display the updated value
        value_str = str(self.params_from_sliders[param_group][key])
        value_str = gui_utils.str_to_len(value_str, disp_len, '0', plus=True)
        self.widget_controls['slider'][key]['value'].setText(value_str)

    def reset_slider_group(self, param_group, redo_plots=False, display_images=True):
        for key, item_sliders in self.sliders[param_group].items():
            self.widget_controls['slider'][key]['data'].setValue(item_sliders['init_ind'])
        if display_images == True:
            self.display_images()
        if redo_plots == True:
            self.redo_plots(calc_range=False)

    def reset_sliders(self):
        self.update_images = False   # dont calc any images/metrics when updating sliders now is slow
        for param_group in self.sliders:
            self.reset_slider_group(param_group, False, False)
        self.update_images = True  # make sure to return to calc images/metrics
        self.display_images()
        self.redo_plots(calc_range=False)

    def set_image_name_text(self):
        for i, data_store in enumerate(self.data_stores):
            res = gui_utils.get_resolutions(data_store)
            self.widget_row[i]['images']['original']['label'].setText(f"{data_store.get_reference_image_name()}\n{res['reference']}")
            self.widget_row[i]['images']['transformed']['label'].setText(f"{gui_utils.get_transformed_image_name(data_store)}\n{res['transform']}")
            for metric_image in data_store.metric_images:
                if metric_image in self.checked_metric_images:
                    metric_name = gui_utils.get_metric_image_name(metric_image, data_store)
                    if len(metric_name) > 20:
                        metric_name = metric_image
                    self.widget_row[i]['metric_images'][metric_image]['label'].setText(metric_name)

    def change_plot_lims(self, state):
        if state == 2:  # 2 is the checked value
            self.plot_data_lim = self.data_lims['range_data']
        else:
            self.plot_data_lim = self.data_lims['fixed']
        self.redo_plots(calc_range=False)


    def change_dataset_name(self, txt):
            ''' change the dataset_name we are using '''
            self.default_dataset_name = txt

    def JND_dataset_range_lower(self, txt):
        ''' change the dataset_name we are using '''
        try:
            self.exp_range_lower = int(txt)
        except:
            return  
        if self.exp_range_lower < 1:
            self.exp_range_lower = 1
        elif self.exp_range_lower > self.exp_range_upper:
            self.exp_range_lower = self.exp_range_upper
        self.widget_controls['label']['range_edit_lower'].setText(
            f"{self.exp_range_lower}")

    def JND_dataset_range_upper(self, txt):
        ''' change the dataset_name we are using '''
        try:
            self.exp_range_upper = int(txt)
        except:
            return
        if self.exp_range_upper < self.exp_range_lower:
            self.exp_range_upper = self.exp_range_lower
        elif self.exp_range_upper > len(self.data_stores[0]):
            self.exp_range_upper = len(self.data_stores[0])
        self.widget_controls['label']['range_edit_upper'].setText(
            f"{self.exp_range_upper}")
    '''
    images settings apply
    '''
    def enable_settings_button(self):
        self.widget_settings['update_button'].setEnabled(True)
        if hasattr(self, 'settings_text_colour_original'):
            self.widget_settings['update_button'].setStyleSheet(
                f"QPushButton {{color: {self.settings_text_colour_original};}}")

    def disable_settings_button(self):
        self.widget_settings['update_button'].setEnabled(False)
        self.widget_settings['update_button'].setStyleSheet(f"QPushButton {{color: gray;}}")

    
    def update_image_settings(self):
        ''' button to apply new image settings '''
        if hasattr(self, 'range_worker'):
            self.range_worker.stop()
        # apply changes to settings
        self.change_pre_processing()
        self.change_post_processing()
        self.change_display_im_size()
        self.change_graph_size()
        self.change_num_steps()
        self.change_display_im_rgb_brightness()
        self.change_display_im_display_brightness()

        self.change_data(0, _redo_plots=False)  # update the image data settings
        self.display_images()
        if hasattr(self, 'update_UI'):
            if self.update_UI == True:
                self.construct_UI()
        if hasattr(self, 'image_settings_update_plots'):
            if self.image_settings_update_plots == True:
                # only redo the graphs if nessesary
                self.redo_plots(calc_range=True)
        self.image_settings_update_plots = False
        self.update_UI = False
        self.disable_settings_button()

    '''
    image settings setters
    '''

    def change_pre_processing(self, *args):
        self.pre_processing_option = self.widget_settings['image_pre_processing']['widget'].currentText(
        )
        for data_store in self.data_stores:
            if hasattr(data_store, 'image_pre_processing'):
                if data_store.image_pre_processing != self.pre_processing_options[self.pre_processing_option]:
                    data_store.image_pre_processing = self.pre_processing_options[
                        self.pre_processing_option]
                    self.image_settings_update_plots = True

    def change_post_processing(self, *args):
        self.post_processing_option = self.widget_settings['image_post_processing']['widget'].currentText(
        )
        for data_store in self.data_stores:
            if hasattr(data_store, 'image_post_processing'):
                if data_store.image_post_processing != self.post_processing_options[self.post_processing_option]:
                    data_store.image_post_processing = self.post_processing_options[
                        self.post_processing_option]
                    self.image_settings_update_plots = True
        # self.display_images()
        # self.redo_plots(calc_range=False)

    def change_display_im_size(self):
        txt = self.widget_settings['image_display_size']['widget'].text()
        if txt == '':
            txt = 1
        new_size = max(1, int(txt))
        if new_size != self.image_display_size:
            self.image_display_size = new_size
            self.update_UI = True
        # self.construct_UI()
        # self.display_images()
        # if old_size > self.image_display_size:
        #     self.setMaximumSize(self.main_widget.sizeHint())
        # if old_size < self.image_display_size:
        #     self.setMinimumSize(self.main_widget.sizeHint())

    def change_graph_size(self):
        txt = self.widget_settings['graph_display_size']['widget'].text()
        if txt == '':
            txt = 1
        new_size = max(1, int(txt))
        if new_size != self.graph_size:
            self.graph_size = new_size
            self.update_UI = True

    def change_num_steps(self):
        txt = self.widget_settings['graph_num_steps']['widget'].text()
        if txt == '':
            txt = 1
        new_steps = max(2, int(txt))
        if new_steps != self.num_steps_range:
            self.num_steps_range = new_steps
            self.update_UI = True
    
    def change_display_im_rgb_brightness(self):
        txt = self.widget_settings['image_display_rgb_brightness']['widget'].text()
        if txt == '':
            txt = 1
        self.rgb_brightness = max(1, int(txt))
    
    def change_display_im_display_brightness(self):
        txt = self.widget_settings['image_display_display_brightness']['widget'].text()
        if txt == '':
            txt = 1
        self.display_brightness = max(1, int(txt))

    '''
    status bar
    '''
    def update_progress(self, v):
        self.pbar.setValue(v)
        if v == 0:
            self.status_bar.showMessage('Done', 3000)

    def update_status_bar(self, v, time=None):
        if time == None:
            self.status_bar.showMessage(v)
        elif isinstance(time, int):
            self.status_bar.showMessage(v, time)

    '''
    export controls
    '''
    def change_text_export_trans(self, trans):
        ''' change colour of text when checkbox is pressed '''
        checked = self.widget_export[trans]['check_box'].isChecked()
        for widget in self.widget_export[trans]:
            if widget == 'check_box':
                pass
            else:
                self.widget_export[trans][widget].setEnabled(checked)
                if checked == True:
                    self.widget_export[trans][widget].setStyleSheet(f"QLineEdit {{color: {self.settings_text_colour_original};}}\nQLabel {{color: {self.settings_text_colour_original};}}")
                else:
                    self.widget_export[trans][widget].setStyleSheet(f"QLineEdit {{color: gray;}}\nQLabel {{color: gray;}}")

    def export_trans_images(self):
        self.export_in_progress = True
        # make save folder
        dir_folder = self.get_export_dir(0)
        save_folder = os.path.join(
            dir_folder, f"images-{str(datetime.datetime.now()).split('.')[0]}")
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # save original image
        ref_image = self.data_stores[0].get_reference_image()
        image_utils.save_image(ref_image,
                               os.path.join(save_folder, f"reference.png"))

        # make and save transforms
        checked_transforms = {}
        for trans in self.widget_export:
            if self.widget_export[trans]['check_box'].isChecked():
                data = {'min': make_float_from_text(self.widget_export[trans]['min_edit'].text()),
                        'max': make_float_from_text(self.widget_export[trans]['max_edit'].text()),
                        'num_steps': int(self.widget_export[trans]['steps_edit'].text()),
                        'function': self.checked_transformations[trans]['function']
                        }
                name = self.widget_export[trans]['name'].text()
                checked_transforms[name] = data

        export_images = plot_utils.get_all_single_transform_params(
            checked_transforms, num_steps='from_dict')

        # remove any params with value 0
        export_images = [x for x in export_images if not x[list(x.keys())[0]] == 0]

        # make and save images
        for single_trans in export_images:
            trans_name = list(single_trans.keys())[0]
            param = single_trans[trans_name]
            img = image_utils.get_transform_image(self.data_stores[0],
                                                  transform_functions={trans_name: self.checked_transformations[trans_name]},
                                                  transform_params={trans_name: param})
            trans_info = {'transform_name': trans_name, 'transform_value': param}
            image_utils.save_image(img, os.path.join(
                save_folder, f'{save_utils.make_name_for_trans(trans_info)}.png'))
        self.status_bar.showMessage(f'Images saved to {save_folder}', 5000)
        self.export_in_progress = False
        self.last_export = save_folder



    def open_mlp_new(self, mpl_canvas):
        fig = gui_utils.break_out_mlp(mpl_canvas)
        fig.show()

    '''
    experiments
    '''
    def change_text_exp_trans(self, trans):
        ''' change colour of text when checkbox is pressed '''
        checked = self.widget_experiment_params[trans]['check_box'].isChecked()
        for widget in self.widget_experiment_params[trans]:
            if widget == 'check_box':
                pass
            else:
                self.widget_experiment_params[trans][widget].setEnabled(checked)
                if checked == True:
                    self.widget_experiment_params[trans][widget].setStyleSheet(f"QLineEdit {{color: {self.settings_text_colour_original};}}\nQLabel {{color: {self.settings_text_colour_original};}}")
                else:
                    self.widget_experiment_params[trans][widget].setStyleSheet(f"QLineEdit {{color: gray;}}\nQLabel {{color: gray;}}")

    def launch_experiment_JND(self):
        '''launch the Just Noticable difference experiment'''
        # first get all the checked transforms and their parameters
        checked_transformation_params = {}
        for trans in self.widget_experiment_params:
            if self.widget_experiment_params[trans]['check_box'].isChecked():
                data = {'min': make_float_from_text(self.widget_experiment_params[trans]['min_edit'].text()),
                        'max': make_float_from_text(self.widget_experiment_params[trans]['max_edit'].text()),
                        'num_steps': int(self.widget_experiment_params[trans]['steps_edit'].text()),
                        'function': self.checked_transformations[trans]['function']}
                name = self.widget_experiment_params[trans]['name'].text()
                checked_transformation_params[name] = data

        # check that we only have one transform selected to JND test to work
        if len(checked_transformation_params) != 1:
            # show message to UI if more than one transform
            self.status_bar.showMessage(
                '!!! Select only one tranform/distortion for Just Noticable Difference Experiment !!!', 10000)
        else:
            # run JND experiment
            self.experiment_JND = IQM_Vis.UI.make_experiment_JND(checked_transformation_params,
                                                                 self.data_stores[0],
                                                                 self.image_display_size,
                                                                 self.rgb_brightness,
                                                                 self.display_brightness,
                                                                 self.default_save_dir,
                                                                 self.default_dataset_name,
                                                                 self.pre_processing_option,
                                                                 self.post_processing_option,
                                                                 self.exp_range_lower,
                                                                 self.exp_range_upper,
                                                                 self.checked_metrics)
            self.experiment_JND.saved_experiment.connect(
                self.change_human_scores_after_exp_JND)
            self.experiment_JND.show()
            self.experiment_JND.showFullScreen()
            

    def launch_experiment_2AFC(self):
        '''Launch the 2 alternate forced choice experiment'''
        # first get all the checked transforms and their parameters
        checked_transformation_params = {}
        for trans in self.widget_experiment_params:
            if self.widget_experiment_params[trans]['check_box'].isChecked():
                data = {'min': make_float_from_text(self.widget_experiment_params[trans]['min_edit'].text()),
                        'max': make_float_from_text(self.widget_experiment_params[trans]['max_edit'].text()),
                        'num_steps': int(self.widget_experiment_params[trans]['steps_edit'].text()),
                        'function': self.checked_transformations[trans]['function']}
                name = self.widget_experiment_params[trans]['name'].text()
                checked_transformation_params[name] = data
        if self.checked_transformations != {}:
            self.experiment_2AFC = IQM_Vis.UI.make_experiment_2AFC(checked_transformation_params,
                                                         self.data_stores[0],
                                                         self.image_display_size,
                                                         self.rgb_brightness,
                                                         self.display_brightness,
                                                         self.default_save_dir,
                                                         self.pre_processing_option,
                                                         self.post_processing_option,
                                                         self.checked_metrics)
            self.experiment_2AFC.saved_experiment.connect(
                self.change_human_scores_after_exp_2AFC)
            self.experiment_2AFC.show()
            self.experiment_2AFC.showFullScreen()
        else:
            self.status_bar.showMessage('Cannot run experiment without transforms', 5000)

    @pyqtSlot(str)
    def change_human_scores_after_exp_2AFC(self, path):
        self._change_human_exp_2AFC(path)

    @pyqtSlot(str)
    def change_human_scores_after_exp_JND(self, path):
        self._change_human_exp_JND(path)


'''
float checking functionality for checkign line edit
'''

def get_float_validator():
    # float_validator = QDoubleValidator()
    # float_validator.setLocale(QLocale('en_US'))  # so comma cannot be used a decimal place for spanish users
    # float_validator.setNotation(QDoubleValidator.Notation(0)) # StandardNotation
    # return float_validator
    return custom_float_validator()

def is_float(input_string):
    # if input_string == '-' or input_string == '+' or input_string == '':
    #     return False
    # pattern = r'^[-+]?[0-9]*\.?[0-9]*$'
    # match = re.match(pattern, input_string)
    # if match:
    #     return True
    # return False
    try: 
        float(input_string)
        return True
    except ValueError:
        return False

def is_almost_float(input_string):
    # if input_string == '-' or input_string == '+' or input_string == '':
    #     return True
    # pattern = r'^[-+]?[0-9]*.*[0-9]$'
    # match = re.match(pattern, input_string)
    # if match:
    #     return True
    # return False
    return True

class custom_float_validator(QValidator):
    def __init__(self, parent=None):
        super(custom_float_validator, self).__init__(parent)

    def validate(self, string, pos):
        if is_float(string):
            return QValidator.State(2), string, pos # Acceptable
        if is_almost_float(string):
            return QValidator.State(1), string, pos # Intermediate
        return QValidator.State(0), string, pos # Invalid

def make_float_from_text(txt):
    # get rid of pesky commas
    no_commas = txt.replace(',', '')
    return float(no_commas)