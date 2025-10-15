import os
from typing import List, Optional, Tuple

import numpy as np
import scipy.stats as scistats
import skimage
import tifffile
import IPython
ipython = IPython.get_ipython()
if ipython:
    ipython.run_line_magic('matplotlib', 'widget')
import IPython.display as IPyd
import ipywidgets as ipyw
import matplotlib.pyplot as plt
from junkie.version import __version__



# You will need this line in your jupyter notebook: %matplotlib widget

class junkie:
    """ 
    junkie: a JUpyter NotebooK Image Explorer
    junkie displays and allows exploration of n-dimensional 
    images in a Jupyter notebook. 
    
    User can interactively change the channel, time point, 
    slice plane ands slice number being viewed. 

    Arguments:
    volume = 2D-5D input image as a numpy array OR file/folder path OR a list of
      numpy arrays and file/folder paths to concatenate sideways (i.e. display 
      side-by-side, but all images in the list must have the same dimensions)
    channel_strs = tuple of strings to distinguish files from different channels 
      (if opening a multichannel image from a file sequence)
    cmap = default('gray'), string for the matplotlib colormap
    figsize = default(4,4), to set the size of the figure
    
    """
    
    next_figure_index: str = 1
    orientations = {'x-y': [0, 1, 2], 'z-x': [1, 2, 0], 'z-y': [2, 1, 0]}
    button_layout = {'width': 'auto', 'height': '32px'}
    button_style = {'font_size': '14px'}
    image_extensions: Tuple[str] = ('.tif', '.tiff', '.jpg', '.jpeg', '.gif', '.png', '.bmp')
    colormaps: List[str] = plt.colormaps()

    def __init__(self, volume: np.ndarray|str, channel_strs: Optional[Tuple[str]] = ('', ), cmap:str = 'gray', figsize: Tuple[int, int] =(4,4)):
        # if volume is a str, read it as an image.
        if isinstance(volume, str):
            volume = junkie.read_image(volume, channel_strs)
            if volume is None:
                # throw exception instead.
                print(f'No volume found at that path. The current path is {os.path.abspath(os.path.curdir)}.')

        if isinstance(volume, list):
            volume_list: List = []
            for avolume in volume:
                if isinstance(avolume, str):
                    loaded_stack = junkie.read_image(avolume, channel_strs)
                    if loaded_stack is not None:
                        volume_list.append(loaded_stack)
                elif isinstance(avolume, np.ndarray):
                    volume_list.append(avolume)
            volume = np.concatenate(np.asarray(volume_list), axis=volume_list[0].ndim-1)

        plt.style.use('dark_background')
        self.volume: np.ndarray = volume
        self.slices: np.ndarray = None

        match self.volume.ndim:
            case 1:
                self.volume = np.expand_dims(self.volume, axis=(0, 1, 2, 3, ))
            case 2:
                self.volume = np.expand_dims(self.volume, axis=(0, 1, 2, ))
            case 3:
                self.volume = np.expand_dims(self.volume, axis=(0, 1, ))
            case 4:
                self.volume = np.expand_dims(self.volume, axis=0)
            case 5:
                pass
            case _:
                print(f"I don't know how to deal with {self.volume.ndim}-dimensional images. But file an issue at https://bitbucket.org/rfg_lab/junkie/issues and someone will teach me.")
                return None

        # image quality control: for images that are not unsigned int, convert to unsigned int with as many bits as necessary for the image range.
        if not self.volume.dtype.kind == 'u':
            self.volume = self.volume.astype(np.uint16)
            im_range = int(np.ceil(self.volume.max()-self.volume.min())) if self.volume.min() < 0. else int(np.ceil(self.volume.max()))
            min_bytes = int(np.ceil(len(bin(im_range)[2:])/8))
            self.volume = self.volume.astype(np.dtype(f'uint{min_bytes*8}'))

        self.color = self.volume[0]
        self.slices = self.color[0]

        self.cmap: str = cmap
        self.figsize: Tuple[int, int] = figsize
        self.pix_val_min_max: List = [np.min(self.color), np.max(self.color)]  # stores min and max pixels values in the current channel.

        # state properties.
        self.axes_visible: bool = True
        self.continuous_update: bool = True
        self.curslice: int = 0
        self.view_plane: str = list(junkie.orientations.keys())[0]

        self.create_UI()

        self.display_slice(True)
   
    def reset_volume(self, reset_range: bool = True):
            self.color = self.volume[self._channel_slider.value]
            self.slices = self.color[self._t_slider.value]

            if reset_range:
                self.pix_val_min_max = [np.min(self.color), np.max(self.color)]            
                self._vmin_slider.max = self._vmax_slider.max = self._vmax_slider.value = self.pix_val_min_max[1]
                self._vmin_slider.value = 0

    def display_slice(self, reset_slices: Optional[bool] = False):
        # Transpose the volume to orient according to the slice plane.
        if reset_slices or self.view_plane != self._plane_selection.value:
            self.view_plane = self._plane_selection.value
            self.image_data = np.transpose(self.slices, junkie.orientations[self.view_plane])
            
            self._Z_slider.max = self.image_data.shape[0]-1 if self.image_data.shape[0]>1 else 1 

            if self.curslice > self._Z_slider.max:
                self._Z_slider.value = 0

            self._vmin_slider.max = self._vmax_slider.max = self.pix_val_min_max[1]

            self._channel_slider.max = self.volume.shape[0]-1 if self.volume.shape[0]>1 else 1
            self._t_slider.max = self.volume.shape[1]-1 if self.volume.shape[1]>1 else 1

            self._setupUI()            
            
            plt.figure(self.fig)
            self.im_axes = plt.imshow(self.image_data[self.curslice,:,:], vmin=self._vmin_slider.value, vmax=self._vmax_slider.value, cmap=self.cmap)

        # Plot slice for the given plane and slice.
        else:
            self.im_axes.set(data=self.image_data[self.curslice, :, :], clim=[self._vmin_slider.value, self._vmax_slider.value], cmap=self.cmap)
        
        self.plot_histogram()

    def create_UI(self):
        # buttons
        # icons from https://fontawesome.com/v4/icons/ or use "description='\uXXXX'" with the unicode symbol.
        self._axes_button = ipyw.ToggleButton(icon='area-chart', layout=junkie.button_layout, style=junkie.button_style, tooltip='axes on/off', value=self.axes_visible)  
        self._axes_button.observe(self._axes_button_click, 'value')

        self._invert_button = ipyw.ToggleButton(icon='shield', layout=junkie.button_layout, style=junkie.button_style, tooltip='invert image', value=False)
        self._invert_button.observe(self._invert_button_click, 'value')

        self._continuousupdate_button = ipyw.ToggleButton(icon='fast-forward', layout=junkie.button_layout, style=junkie.button_style, tooltip='update continuously', value=self.continuous_update)
        self._continuousupdate_button.observe(self._continuousupdate_button_click, 'value')

        self._fliph_button = ipyw.Button(icon='arrows-h', layout=junkie.button_layout, style=junkie.button_style, tooltip='flip horizontal')
        self._fliph_button.on_click(self._flip_button_click)

        self._flipv_button = ipyw.Button(icon='arrows-v', layout=junkie.button_layout, style=junkie.button_style, tooltip='flip vertical')
        self._flipv_button.on_click(self._flip_button_click)

        self._rotate_button = ipyw.Button(icon='refresh', layout=junkie.button_layout, style=junkie.button_style, tooltip='rotate 90º clockwise')
        self._rotate_button.on_click(self._rotate_button_click)

        self._channel_slider = ipyw.IntSlider(min=0, max=self.volume.shape[0]-1, step=1, continuous_update=self.continuous_update, 
            description='channel:')
        self._channel_slider.observe(self._channel_slider_change, 'value')

        self._t_slider = ipyw.IntSlider(min=0, max=self.volume.shape[1]-1, step=1, continuous_update=self.continuous_update, 
            description='time point:')
        self._t_slider.observe(self._t_slider_change, 'value')

        self._Z_slider = ipyw.IntSlider(min=0, max=self.slices.shape[0]-1, step=1, continuous_update=self.continuous_update, 
            description='image slice:')
        self._Z_slider.observe(self._Z_slider_change, 'value')

        self._plane_selection = ipyw.RadioButtons(
            options=['x-y','z-y', 'z-x'], value='x-y', 
            description='slicing plane:', disabled=False,
            style={'description_width': 'initial'})
        self._plane_selection.observe(self._view_change, 'value')

        self._vmin_slider = ipyw.IntSlider(min=0, max=self.pix_val_min_max[1], step=1, continuous_update=self.continuous_update, 
            description='minimum pixel value:', style={'description_width': 'auto'})
        self._vmin_slider.observe(self._vmin_slider_change)
        self._vmax_slider = ipyw.IntSlider(min=0, max=self.pix_val_min_max[1], step=1, continuous_update=self.continuous_update, 
            description='maximum pixel value:', style={'description_width': 'auto'})
        self._vmax_slider.value = self.pix_val_min_max[1]
        self._vmax_slider.observe(self._vmax_slider_change, 'value')

        self._autocontrast_button = ipyw.Button(description='auto', layout=junkie.button_layout, style=junkie.button_style, tooltip='auto contrast')
        self._autocontrast_button.on_click(self._autocontrast_button_click)

        self._colormap_dropdown = ipyw.Dropdown(options=junkie.colormaps, value=self.cmap, tooltip='colormap')
        self._colormap_dropdown.observe(self._colormap_dropdown_change, 'value')

        self.fig = plt.figure(junkie.next_figure_index, figsize=self.figsize)
        junkie.next_figure_index += 1
        self.im_axes = None

        self.fig.canvas.header_visible = False  # remove the figure number; handle functions in canvas could be useful to control interaction.
        # self.fig.canvas.toolbar_visible = False

        plt.ioff()  # this is here so that the figure is not plotted twice (once when created, because %matplotlib widget, and a second time when added to the HBox).
        self.hist_fig = plt.figure(junkie.next_figure_index, figsize=(2, 1), facecolor='white')
        junkie.next_figure_index += 1
        self.hist_fig.canvas.header_visible = False
        self.hist_fig.canvas.toolbar_visible = False
        self.hist_fig.canvas.footer_visible = False
        plt.ion()

        self.hist_widget = self.hist_fig.canvas

        self.new_toolbar = ipyw.HBox([ipyw.VBox([ipyw.HBox([ipyw.VBox([self._channel_slider, self._t_slider, self._Z_slider]), self._plane_selection, ipyw.VBox([self._vmin_slider, self._vmax_slider, ipyw.HBox([self._autocontrast_button, self._colormap_dropdown])])]), ipyw.HBox([self._rotate_button, self._fliph_button, self._flipv_button, self._invert_button, self._axes_button, self._continuousupdate_button])]), self.hist_widget])

        IPyd.display(self.new_toolbar)
        

    # Enables/disables UI components.
    def _setupUI(self):
        self._channel_slider.disabled = False if self.volume.shape[0] > 1 else True
        self._t_slider.disabled = False if self.volume.shape[1] > 1 else True
        self._Z_slider.disabled = False if self.slices.shape[0] > 1 else True
        self._plane_selection.disabled = False if self.slices.shape[0] > 1 else True

    def plot_histogram(self):
        plt.figure(self.hist_fig)
        plt.clf()
        plt.hist(self.image_data[self.curslice].ravel(), int(self.pix_val_min_max[1]), density=True, color='purple')
        plt.gca().set_facecolor('white')
        plt.xlim([-5, 260])

        max_y = plt.gca().get_ylim()[1]

        plt.plot([self._vmin_slider.value, self._vmin_slider.value], [0, max_y], color='red')
        plt.plot([self._vmax_slider.value, self._vmax_slider.value], [0, max_y], color='cyan')

    def _axes_button_click(self, b):
        if self.axes_visible:
            self.fig.axes[0].set_axis_off()
        else:
            self.fig.axes[0].set_axis_on()   

        self.axes_visible = not self.axes_visible

    def _invert_button_click(self, b):
        if self.cmap.endswith("_r"):
            self.cmap = self.cmap[:-2]
        else:
            self.cmap += "_r"

        self._colormap_dropdown.value=self.cmap

    def _flip_button_click(self, b):
        if b is self._fliph_button:
            self.volume = self.volume[..., ::-1]
        elif b is self._flipv_button:
            self.volume = self.volume[..., ::-1, :]

        self.reset_volume(False)
        self.display_slice(True)

    def _rotate_button_click(self, b):
        self.volume = np.rot90(self.volume, -1, (3, 4))

        self.reset_volume(False)
        self.display_slice(True)

    def _autocontrast_button_click(self, b):
        low = scistats.mode(self.image_data[self.curslice,:,:].ravel())[0]
        high = int(np.percentile(self.image_data[self.curslice,:,:], 99))

        self._vmin_slider.value = low
        self._vmax_slider.value = high

        old_update = self.continuous_update
        self.continuous_update = True
        
        self._vmin_slider_change(None)
        self._vmax_slider_change(None)

        self.continuous_update = old_update

    def _continuousupdate_button_click(self, b):
        self.continuous_update = not self.continuous_update
        
        self._channel_slider.continuous_update = self.continuous_update
        self._t_slider.continuous_update = self.continuous_update
        self._Z_slider.continuous_update = self.continuous_update
        self._vmin_slider.continuous_update = self.continuous_update
        self._vmax_slider.continuous_update = self.continuous_update

    def _Z_slider_change(self, change):
        if not self._Z_slider.disabled:
            self.curslice = self._Z_slider.value
            self.display_slice()

    def _t_slider_change(self, change):
        if not self._t_slider.disabled:
            self.slices = self.color[self._t_slider.value]
            self.display_slice(True)

    def _channel_slider_change(self, change):
        if not self._channel_slider.disabled:
            self.reset_volume(True)
            self.display_slice(True)

    def _view_change(self, change):
        self.display_slice(True)

    def _vmin_slider_change(self, change):
        if self._vmin_slider.value > self._vmax_slider.value:
            self._vmax_slider.value = self._vmin_slider.value

        #self.pix_val_min_max[0], self.pix_val_min_max[1] = self._vmin_slider.value, self._vmax_slider.value  # this used to be commented out ... check back in case of problems.  
        self.display_slice()

    def _vmax_slider_change(self, change):
        if self._vmax_slider.value < self._vmin_slider.value:
            self._vmin_slider.value = self._vmax_slider.value

        #self.pix_val_min_max[0], self.pix_val_min_max[1] = self._vmin_slider.value, self._vmax_slider.value  # this used to be commented out ... check back in case of problems.  
        self.display_slice()

    def _colormap_dropdown_change(self, change):
        self.cmap = self._colormap_dropdown.value

        self.display_slice()

    @classmethod
    def read_image(cls, file_path: str, channel_strs: Optional[Tuple[str]]=('',)) -> Optional[np.ndarray]:
        im: np.ndarray = None

        if os.path.isfile(file_path):        
            _, ext = os.path.splitext(file_path)

            # First try to read images within the allowed extensions.
            if str.lower(ext) in junkie.image_extensions:
                im = skimage.io.imread(file_path)
            # If the extension is unknown, try to read as a tiff file.
            else:
                try:
                    im = tifffile.imread(file_path)
                except Exception:
                    return None
        
            # Multi-channel images: shift the number of channels (im.shape[2]) to the first dimension.
            if im.ndim == 3 and (im.shape[2] == 3 or im.shape[2] == 4): # without (3) or with (4) alpha channel
                im = np.rollaxis(im, 2) # ignore the alpha channel if there were one.

            # Multi-channel time series.
            elif im.ndim == 4:
                # shift the number of channels (im.shape[2]) to the first dimension.
                im = np.rollaxis(im, 3)

                #volume_list: list = []
                #for achannel in im:
                #    volume_list.append(achannel)
                #
                #im = np.concatenate(np.asarray(volume_list), axis=volume_list[0].ndim-1)

        elif os.path.isdir(file_path):
            channels: List[np.ndarray] = [[] for _ in channel_strs]

            for filename in os.listdir(file_path):
                img = junkie.read_image(os.path.join(file_path, filename))

                if img is not None:
                    index_list = [theindex for theindex in range(len(channel_strs)) if channel_strs[theindex] in filename]

                    if index_list != []:
                        channels[index_list[0]].append(img)

            im = np.asarray(channels)

        return im
