"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
import wx
import numpy as np
import numpy.ma as ma
from bisect import bisect_left
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, ListedColormap, BoundaryNorm
from collections import OrderedDict
import typing
import io
import logging

from .PyTranslate import _
from .CpGrid import CpGrid
from .PyVertex import getRGBfromI, getIfromRGB


class wolfpalette(wx.Frame, LinearSegmentedColormap):
    """
    Palette de couleurs basée sur l'objet "LinearSegmentedColormap" de Matplotlib (Colormap objects based on lookup tables using linear segments)
    """
    filename: str
    nb: int
    colors: np.array
    colorsflt: np.array
    colorsuint8: np.array

    def __init__(self, parent=None, title=_('Colormap'), w=100, h=500, nseg=1024):

        self.filename = ''
        self.nb = 0
        self.values = None
        self.colormin = np.array([1., 1., 1., 1.])
        self.colormax = np.array([0, 0, 0, 1.])
        self.nseg = nseg
        self.automatic = True
        self.interval_cst = False
        self.colors = np.zeros((self.nb, 4), dtype=np.float64)
        self.values = np.zeros((self.nb), dtype=np.float64)

        self.wx_exists = wx.App.Get() is not None

        # Appel à l'initialisation d'un frame général
        if (self.wx_exists):
            wx.Frame.__init__(self, parent, title=title, size=(w, h), style=wx.DEFAULT_FRAME_STYLE)

        LinearSegmentedColormap.__init__(self, 'wolf', {}, nseg)
        self.set_bounds()

    def __getstate__(self):
        """ Récupération de l'état de l'objet pour la sérialisation """
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        """ Récupération de l'état de l'objet pour la désérialisation """
        self.__dict__.update(state)

        # Reinitialize the LinearSegmentedColormap with the current state
        self.fill_segmentdata()

    @property
    def colormin_uint8(self):
        return self.colormin.astype(np.uint8)*255

    @property
    def colormax_uint8(self):
        return self.colormax.astype(np.uint8)*255

    def get_colors_f32(self):

        colors = self.colorsflt[:, :3].astype(np.float32)

        return colors

    def get_colors_uint8(self):

        colors = self.colorsflt[:, :3].astype(np.uint8) * 255

        return colors

    def set_bounds(self):
        self.set_under(tuple(self.colormin))
        self.set_over(tuple(self.colormax))

    def get_rgba(self, x: np.ndarray):
        """Récupération de la couleur en fonction de la valeur x

        :param x: tableau de valeurs
        """

        dval = self.values[-1]-self.values[0]
        if dval == 0.:
            dval = 1.
        xloc = (x-self.values[0])/dval

        if self.interval_cst:
            rgba = np.ones((xloc.shape[0], xloc.shape[1], 4), dtype=np.uint8)

            ij = np.where(xloc < 0.)
            rgba[ij[0], ij[1]] = self.colormin_uint8
            ij = np.where(xloc >= 1.)
            rgba[ij[0], ij[1]] = self.colormax_uint8

            for i in range(self.nb-1):
                val1 = (self.values[i]-self.values[0])/dval
                val2 = (self.values[i+1]-self.values[0])/dval
                # c1   = self.colorsflt[i]
                c1 = self.colorsuint8[i]
                ij = np.where((xloc >= val1) & (xloc < val2))
                rgba[ij[0], ij[1]] = c1

            return rgba
        else:
            return self(xloc, bytes=True)

    def get_rgba_oneval(self, x: float):
        """Récupération de la couleur en fonction de la valeur x"""

        dval = self.values[-1]-self.values[0]
        if dval == 0.:
            dval = 1.
        xloc = (x-self.values[0])/dval

        if self.interval_cst:
            rgba = np.ones((4), dtype=np.uint8)

            if xloc < 0.:
                rgba = self.colormin_uint8
            elif xloc >= 1.:
                rgba = self.colormax_uint8
            else:
                for i in range(self.nb-1):
                    val1 = (self.values[i]-self.values[0])/dval
                    val2 = (self.values[i+1]-self.values[0])/dval
                    if (xloc >= val1) & (xloc < val2):
                        c1 = self.colorsuint8[i]
                        rgba = c1
                        break

            return rgba
        else:
            return self(xloc, bytes=True)

    def export_palette_matplotlib(self, name):
        cmaps = OrderedDict()
        cmaps['Perceptually Uniform Sequential'] = ['viridis', 'plasma', 'inferno', 'magma', 'cividis']

        cmaps['Sequential'] = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr',
                               'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']
        cmaps['Sequential (2)'] = ['binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink', 'spring',
                                   'summer', 'autumn', 'winter', 'cool', 'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper']
        cmaps['Diverging'] = ['PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                              'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']
        cmaps['Cyclic'] = ['twilight', 'twilight_shifted', 'hsv']
        cmaps['Qualitative'] = ['Pastel1', 'Pastel2', 'Paired', 'Accent',
                                'Dark2', 'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c']
        cmaps['Miscellaneous'] = ['flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern', 'gnuplot',
                                  'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar']

        for cmap_category, cmap_list in cmaps.items():
            if (name in cmaps[cmap_category]):
                self = plt.get_cmap(name)
                self.nb = len(self._segmentdata['blue'])
                self.values = np.linspace(0., 1., self.nb, dtype=np.float64)
                self.colorsflt = np.zeros((self.nb, 4), dtype=np.float64)
                for i in range(self.nb):
                    self.colorsflt[i, 0] = self._segmentdata['red'][i][2]
                    self.colorsflt[i, 1] = self._segmentdata['green'][i][2]
                    self.colorsflt[i, 2] = self._segmentdata['blue'][i][2]
                    self.colorsflt[i, 3] = self._segmentdata['alpha'][i][2]
                test = 1
                break
            else:
                test = 1

        return self.nb, self.values, self._segmentdata, self.colorsflt

    def distribute_values(self, minval: float = -99999, maxval: float = -99999, step=0, wx_permitted=True):
        """ Distribution des valeurs de la palette

        :param minval: valeur minimale
        :param maxval: valeur maximale
        :param step: pas de distribution

        Si le pas est fourni, il prend le dessus sur la valeur maximale.

        """

        if self.wx_exists and wx_permitted:
            if minval == -99999:
                dlg = wx.TextEntryDialog(None, _('Minimum value'), value=str(self.values[0]))
                ret = dlg.ShowModal()

                try:
                    self.values[0] = float(dlg.GetValue())
                except:
                    logging.warning('Bad value for minimum - No change')

                dlg.Destroy()
            else:
                self.values[0] = minval

            if maxval == -99999 and step == 0:

                dlg = wx.MessageDialog(None, _('Would you like to set the incremental step value ?'),
                                       style=wx.YES_NO | wx.YES_DEFAULT)
                ret = dlg.ShowModal()
                dlg.Destroy
                if ret == wx.ID_YES:
                    dlg = wx.TextEntryDialog(None, _('Step value'), value='1')
                    ret = dlg.ShowModal()

                    try:
                        step = float(dlg.GetValue())
                    except:
                        logging.warning('Bad value for step - using default value 0.1 m')
                        step = 0.1

                    dlg.Destroy()
                else:
                    dlg = wx.TextEntryDialog(None, _('Maximum value'), value=str(self.values[-1]))
                    ret = dlg.ShowModal()

                    try:
                        self.values[-1] = float(dlg.GetValue())
                    except:
                        logging.warning('Bad value for maximum - using min value + 1 m')
                        self.values[-1] = self.values[0] + 1.

                    dlg.Destroy()

            elif maxval != -99999:
                self.values[-1] = maxval
        else:
            if minval != -99999:
                self.values[0] = minval
            if maxval != -99999:
                self.values[-1] = maxval

        if step == 0:
            self.values = np.linspace(self.values[0], self.values[-1], num=self.nb,
                                      endpoint=True, dtype=np.float64)[0:self.nb]
        else:
            self.values = np.arange(self.values[0], self.values[0]+(self.nb)*step, step, dtype=np.float64)[0:self.nb]

        self.fill_segmentdata()

    def get_ScalarMappable_mpl(self):
        """ Récupération de l'objet ScalarMappable via Matplotlib """
        if self.interval_cst:
            discrete_cmap = ListedColormap(self.colorsflt[:, :3])
            colorbar = ScalarMappable(BoundaryNorm(self.values, ncolors=self.nb-1), cmap=discrete_cmap)
            return colorbar
        else:
            return ScalarMappable(Normalize(self.values[0], self.values[-1]), cmap=self)

    def export_image(self, fn='', h_or_v: typing.Literal['h', 'v', ''] = '', figax=None):
        """
        Export image from colormap

        :param : fn : filepath or io.BytesIO()
        :param : h_or_v : configuration to save 'h' = horizontal, 'v' = vertical, '' = both
        """
        if self.values is None:
            logging.warning('No values in palette - Nothing to do !')
            return None, None

        if len(self.values) ==0:
            logging.warning('No values in palette - Nothing to do !')
            logging.info(_('Do you have defined the palette values ?'))
            logging.info(_('If yes, please check your Global Options. You may not have defined the correct palette to use.'))
            return None, None

        if fn == '':
            file = wx.FileDialog(None, "Choose .pal file", wildcard="png (*.png)|*.png|all (*.*)|*.*", style=wx.FD_SAVE)
            if file.ShowModal() == wx.ID_CANCEL:
                return
            else:
                # récupération du nom de fichier avec chemin d'accès
                fn = file.GetPath()

        if h_or_v == 'v':

            if figax is None:
                fig, ax = plt.subplots(1, 1)
            else:
                fig, ax = figax

            if self.interval_cst:
                discrete_cmap = ListedColormap(self.colorsflt[:, :3])
                colorbar = plt.colorbar(ScalarMappable(BoundaryNorm(self.values, ncolors=self.nb-1),
                                                      cmap=discrete_cmap),
                            cax=ax,
                            orientation='vertical',
                            extend='both',
                            aspect=20,
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')

            else:
                plt.colorbar(ScalarMappable(Normalize(self.values[0],
                                                      self.values[-1]),
                                                      cmap=self),
                            cax=ax,
                            orientation='vertical',
                            extend='both',
                            aspect=20,
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')

            plt.tick_params(labelsize=14)
            if figax is None:
                fig.set_size_inches((2, 10))
                fig.tight_layout()

            if fn != '' and fn is not None:
                plt.savefig(fn, format='png')
            # plt.savefig(fn,bbox_inches='tight', format='png')
        elif h_or_v == 'h':
            if figax is None:
                fig, ax = plt.subplots(1, 1)
            else:
                fig, ax = figax

            if self.interval_cst:
                discrete_cmap = ListedColormap(self.colorsflt[:, :3])
                colorbar = plt.colorbar(ScalarMappable(BoundaryNorm(self.values, ncolors=self.nb-1),
                                                      cmap=discrete_cmap),
                            cax=ax,
                            orientation='horizontal',
                            extend='both',
                            aspect=20,
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')
            else:
                plt.colorbar(ScalarMappable(Normalize(self.values[0], self.values[-1]), cmap=self),
                            cax=ax,
                            orientation='horizontal',
                            extend='both',
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')

            plt.tick_params(labelsize=14, rotation=45)
            if figax is None:
                fig.set_size_inches((2, 10))
                fig.tight_layout()
            if fn != '' and fn is not None:
                plt.savefig(fn, format='png')
            # plt.savefig(fn,bbox_inches='tight', format='png')
        else:
            if isinstance(fn, io.BytesIO):
                logging.warning('Bad type for "fn" - Nothing to do !')
                return

            if figax is None:
                fig, ax = plt.subplots(1, 1)
            else:
                fig, ax = figax

            if self.interval_cst:
                discrete_cmap = ListedColormap(self.colorsflt[:, :3])
                colorbar = plt.colorbar(ScalarMappable(BoundaryNorm(self.values, ncolors=self.nb-1),
                                                      cmap=discrete_cmap),
                            cax=ax,
                            orientation='vertical',
                            extend='both',
                            aspect=20,
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')
            else:
                plt.colorbar(ScalarMappable(Normalize(self.values[0], self.values[-1]), cmap=self),
                            cax=ax,
                            orientation='vertical',
                            extend='both',
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')
            plt.tick_params(labelsize=14)
            fig.set_size_inches((2, 10))
            fig.tight_layout()
            if fn != '' and fn is not None:
                plt.savefig(fn[:-4]+'_v.png', format='png')

            if figax is None:
                fig, ax = plt.subplots(1, 1)
            else:
                fig, ax = figax

            if self.interval_cst:
                discrete_cmap = ListedColormap(self.colorsflt[:, :3])
                colorbar = plt.colorbar(ScalarMappable(BoundaryNorm(self.values, ncolors=self.nb-1),
                                                      cmap=discrete_cmap),
                            cax=ax,
                            orientation='horizontal',
                            extend='both',
                            aspect=20,
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')
            else:
                plt.colorbar(ScalarMappable(Normalize(self.values[0], self.values[-1]), cmap=self),
                            cax=ax,
                            orientation='horizontal',
                            extend='both',
                            spacing='proportional',
                            ticks=self.values,
                            format='%.3f')
            plt.tick_params(labelsize=14, rotation=45)
            fig.set_size_inches((10, 2))
            fig.tight_layout()
            if fn != '' and fn is not None:
                plt.savefig(fn[:-4]+'_h.png', format='png')

        fig.set_visible(False)

        return fig, ax

    def plot(self, fig: Figure, ax: plt.Axes):
        """ Affichage de la palette de couleurs """

        gradient = np.linspace(0, 1, 256)
        gradient = np.vstack((gradient, gradient))

        pos = []
        txt = []
        dval = (self.values[-1]-self.values[0])
        if dval == 0.:
            dval = 1.

        if self.interval_cst:
            discrete_cmap = ListedColormap(self.colorsflt[:, :3])
            ax.imshow(gradient, aspect='auto', cmap=discrete_cmap)

            for idx, curval in enumerate(self.values):
                pos.append(idx/self.nb*256.)
                txt.append("{0:.3f}".format(curval))
        else:
            ax.imshow(gradient, aspect='auto', cmap=self)

            for curval in self.values:
                pos.append((curval-self.values[0])/dval*256.)
                txt.append("{0:.3f}".format(curval))

        ax.set_yticklabels([])
        ax.set_xticks(pos)
        ax.set_xticklabels(txt, rotation=30, fontsize=6)

    @property
    def cmap(self):
        """ Récupération de la palette de couleurs """
        return self

    @property
    def vmin(self):
        """ Récupération de la valeur minimale """
        return self.values[0]

    @property
    def vmax(self):
        """ Récupération de la valeur maximale """
        return self.values[-1]

    @property
    def norm(self):
        """ Récupération de la normalisation """
        return Normalize(self.values[0], self.values[-1])

    def fillgrid(self, gridto: CpGrid):
        """ Remplissage d'une grille avec les valeurs de la palette """

        gridto.SetColLabelValue(0, 'Value')
        gridto.SetColLabelValue(1, 'R')
        gridto.SetColLabelValue(2, 'G')
        gridto.SetColLabelValue(3, 'B')

        nb = gridto.GetNumberRows()
        if len(self.values)-nb > 0:
            gridto.AppendRows(len(self.values)-nb)

        k = 0
        for curv, rgba in zip(self.values, self.colors):
            gridto.SetCellValue(k, 0, str(curv))
            gridto.SetCellValue(k, 1, str(rgba[0]))
            gridto.SetCellValue(k, 2, str(rgba[1]))
            gridto.SetCellValue(k, 3, str(rgba[2]))
            k += 1

        nb = gridto.GetNumberRows()
        while k < nb:
            gridto.SetCellValue(k, 0, '')
            gridto.SetCellValue(k, 1, '')
            gridto.SetCellValue(k, 2, '')
            gridto.SetCellValue(k, 3, '')
            k += 1

    def updatefromgrid(self, gridfrom: CpGrid):
        """ Mise à jour de la palette sur base d'une grille """

        nbl = gridfrom.GetNumberRows()

        for i in range(nbl):
            if gridfrom.GetCellValue(i, 0) == '':
                nbl = i-1
                break

        if i < self.nb:
            self.nb = i
            self.values = self.values[0:i]
            self.colors = self.colors[0:i, :]
        else:
            self.nb = i
            oldvalues = self.values
            oldcolors = self.colors
            self.values = np.zeros(self.nb, dtype=np.float64)
            self.colors = np.zeros((self.nb, 4), dtype=int)
            self.values[0:len(oldvalues)] = oldvalues
            self.colors[0:len(oldcolors), :] = oldcolors

        update = False

        for k in range(self.nb):

            update = update or self.values[k] != float(gridfrom.GetCellValue(k, 0))
            update = update or self.colors[k, 0] != float(gridfrom.GetCellValue(k, 1))
            update = update or self.colors[k, 1] != float(gridfrom.GetCellValue(k, 2))
            update = update or self.colors[k, 2] != float(gridfrom.GetCellValue(k, 3))

            self.values[k] = float(gridfrom.GetCellValue(k, 0))
            self.colors[k, 0] = int(gridfrom.GetCellValue(k, 1))
            self.colors[k, 1] = int(gridfrom.GetCellValue(k, 2))
            self.colors[k, 2] = int(gridfrom.GetCellValue(k, 3))

        self.fill_segmentdata()

        return update

    def updatefrompalette(self, srcpal):
        """
        Mise à jour de la palette sur base d'une autre

        On copie les valeurs, on ne pointe pas l'objet
        """

        for k in range(len(srcpal.values)):
            self.values[k] = srcpal.values[k]

        self.fill_segmentdata()

    def lookupcolor(self, x):
        if x < self.values[0]:
            return wx.Colour(self.colormin)
        if x > self.values[-1]:
            return wx.Colour(self.colormax)

        i = bisect_left(self.values, x)
        k = (x - self.values[i-1])/(self.values[i] - self.values[i-1])

        r = int(k*(float(self.colors[i, 0]-self.colors[i-1, 0]))) + self.colors[i-1, 0]
        g = int(k*(float(self.colors[i, 1]-self.colors[i-1, 1]))) + self.colors[i-1, 1]
        b = int(k*(float(self.colors[i, 2]-self.colors[i-1, 2]))) + self.colors[i-1, 2]
        a = int(k*(float(self.colors[i, 3]-self.colors[i-1, 3]))) + self.colors[i-1, 3]

        y = wx.Colour(r, g, b, a)

        return y

    def lookupcolorflt(self, x):
        if x < self.values[0]:
            return wx.Colour(self.colormin)
        if x > self.values[-1]:
            return wx.Colour(self.colormax)

        i = bisect_left(self.values, x)
        k = (x - self.values[i-1])/(self.values[i] - self.values[i-1])

        r = k*(self.colorsflt[i, 0]-self.colorsflt[i-1, 0]) + self.colorsflt[i-1, 0]
        g = k*(self.colorsflt[i, 1]-self.colorsflt[i-1, 1]) + self.colorsflt[i-1, 1]
        b = k*(self.colorsflt[i, 2]-self.colorsflt[i-1, 2]) + self.colorsflt[i-1, 2]
        a = k*(self.colorsflt[i, 3]-self.colorsflt[i-1, 3]) + self.colorsflt[i-1, 3]

        y = [r, g, b, a]
        return y

    def lookupcolorrgb(self, x):
        if x < self.values[0]:
            return wx.Colour(self.colormin)
        if x > self.values[-1]:
            return wx.Colour(self.colormax)

        i = bisect_left(self.values, x)
        k = (x - self.values[i-1])/(self.values[i] - self.values[i-1])

        r = int(k*(float(self.colors[i, 0]-self.colors[i-1, 0]))) + self.colors[i-1, 0]
        g = int(k*(float(self.colors[i, 1]-self.colors[i-1, 1]))) + self.colors[i-1, 1]
        b = int(k*(float(self.colors[i, 2]-self.colors[i-1, 2]))) + self.colors[i-1, 2]
        a = int(k*(float(self.colors[i, 3]-self.colors[i-1, 3]))) + self.colors[i-1, 3]

        return r, g, b, a

    def default16(self):
        """Palette 16 coulrurs par défaut dans WOLF"""

        self.nb = 16
        self.values = np.linspace(0., 1., 16, dtype=np.float64)
        self.colors = np.zeros((self.nb, 4), dtype=int)
        self.colorsflt = np.zeros((self.nb, 4), dtype=np.float64)

        self.colors[0, :] = [128, 255, 255, 255]
        self.colors[1, :] = [89, 172, 255, 255]
        self.colors[2, :] = [72, 72, 255, 255]
        self.colors[3, :] = [0, 0, 255, 255]
        self.colors[4, :] = [0, 128, 0, 255]
        self.colors[5, :] = [0, 221, 55, 255]
        self.colors[6, :] = [128, 255, 128, 255]
        self.colors[7, :] = [255, 255, 0, 255]
        self.colors[8, :] = [255, 128, 0, 255]
        self.colors[9, :] = [235, 174, 63, 255]
        self.colors[10, :] = [255, 0, 0, 255]
        self.colors[11, :] = [209, 71, 12, 255]
        self.colors[12, :] = [128, 0, 0, 255]
        self.colors[13, :] = [185, 0, 0, 255]
        self.colors[14, :] = [111, 111, 111, 255]
        self.colors[15, :] = [192, 192, 192, 255]

        self.fill_segmentdata()

    def default_difference3(self):
        """ Palette 3 couleurs pour les différences par défaut dans WOLF """
        self.nb = 3
        self.values = np.asarray([-10., 0., 10.], dtype=np.float64)
        self.colors = np.zeros((self.nb, 4), dtype=int)
        self.colorsflt = np.zeros((self.nb, 4), dtype=np.float64)
        self.colors[0, :] = [0, 0, 255, 255]   # Bleu
        self.colors[1, :] = [255, 255, 255, 255]  # Blanc
        self.colors[2, :] = [255, 0, 0, 255]   # Rouge
        self.fill_segmentdata()

    def set_values_colors(self,
                          values: typing.Union[list[float], np.ndarray],
                          colors: typing.Union[list[tuple[int]], np.ndarray]):
        """ Mise à jour des valeurs et couleurs de la palette """

        assert len(values) == len(colors), "Length of values and colors must be the same"
        assert len(values) > 1, "At least 2 values are required"
        assert len(colors[0]) in [3, 4], "Colors must be in RGB or RGBA format"

        self.nb = len(values)
        self.values = np.asarray(values, dtype=np.float64)

        self.colors = np.zeros((self.nb, 4), dtype=int)
        self.colorsflt = np.zeros((self.nb, 4), dtype=np.float64)

        if isinstance(colors, list):
            if len(colors[0]) == 3:
                for curcol in range(self.nb):
                    self.colors[curcol, 0] = colors[curcol][0]
                    self.colors[curcol, 1] = colors[curcol][1]
                    self.colors[curcol, 2] = colors[curcol][2]
                    self.colors[curcol, 3] = 255
            elif len(colors[0]) == 4:
                for curcol in range(self.nb):
                    self.colors[curcol, 0] = colors[curcol][0]
                    self.colors[curcol, 1] = colors[curcol][1]
                    self.colors[curcol, 2] = colors[curcol][2]
                    self.colors[curcol, 3] = colors[curcol][3]
        elif isinstance(colors, np.ndarray):
            if colors.shape[1] == 3:
                for curcol in range(self.nb):
                    self.colors[curcol, 0] = colors[curcol, 0]
                    self.colors[curcol, 1] = colors[curcol, 1]
                    self.colors[curcol, 2] = colors[curcol, 2]
                    self.colors[curcol, 3] = 255
            elif colors.shape[1] == 4:
                for curcol in range(self.nb):
                    self.colors[curcol, 0] = colors[curcol, 0]
                    self.colors[curcol, 1] = colors[curcol, 1]
                    self.colors[curcol, 2] = colors[curcol, 2]
                    self.colors[curcol, 3] = colors[curcol, 3]

        self.fill_segmentdata()

    def set_values(self,
                   values: typing.Union[list[float], np.ndarray]):
        """ Mise à jour des valeurs de la palette """

        assert len(values) == self.nb, "Length of values must match the number of colors"

        self.values = np.asarray(values, dtype=np.float64)

        self.fill_segmentdata()

    def defaultgray(self):
        """Palette grise par défaut dans WOLF"""

        self.nb = 3
        self.values = np.asarray([0., 0.5, 1.], dtype=np.float64)
        self.colors = np.asarray([[0, 0, 0, 255], [128, 128, 128, 255], [255, 255, 255, 255]], dtype=np.int32)

        # self.nb = 11
        # self.values = np.asarray([0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.], dtype=np.float64)
        # self.colors = np.asarray([[0, 0, 0, 255],
        #                           [22, 22, 22, 255],
        #                             [44, 44, 44, 255],
        #                             [66, 66, 66, 255],
        #                             [88, 88, 88, 255],
        #                             [110, 110, 110, 255],
        #                             [132, 132, 132, 255],
        #                             [154, 154, 154, 255],
        #                             [176, 176, 176, 255],
        #                             [198, 198, 198, 255],
        #                             [255, 255, 255, 255]], dtype=np.int32)

        self.fill_segmentdata()

    def fill_segmentdata(self):
        """Mise à jour de la palatte de couleurs"""

        self.colorsflt = self.colors.astype(float)/255.
        self.colorsuint8 = self.colors.astype(np.uint8)

        if self.nb > 1:

            dval = self.values[-1]-self.values[0]

            normval = np.ones([len(self.values)])

            if dval > 0.:
                normval = (self.values-self.values[0])/dval

            normval[0] = 0.
            normval[-1] = 1.
            segmentdata = {"red": np.column_stack([normval, self.colorsflt[:, 0], self.colorsflt[:, 0]]),
                        "green": np.column_stack([normval, self.colorsflt[:, 1], self.colorsflt[:, 1]]),
                        "blue": np.column_stack([normval, self.colorsflt[:, 2], self.colorsflt[:, 2]]),
                        "alpha": np.column_stack([normval, self.colorsflt[:, 3], self.colorsflt[:, 3]])}

            LinearSegmentedColormap.__init__(self, 'wolf', segmentdata, self.nseg)

    def readfile(self, *args):
        """Lecture de la palette sur base d'un fichier WOLF .pal"""
        if len(args) > 0:
            # s'il y a un argument on le prend tel quel
            self.filename = str(args[0])
        else:
            if self.wx_exists:
                # ouverture d'une boîte de dialogue
                file = wx.FileDialog(None, "Choose .pal file", wildcard="pal (*.pal)|*.pal|all (*.*)|*.*")
                if file.ShowModal() == wx.ID_CANCEL:
                    file.Destroy()
                    return
                else:
                    # récuparétaion du nom de fichier avec chemin d'accès
                    self.filename = file.GetPath()
                    file.Destroy()
            else:
                return

        # lecture du contenu
        with open(self.filename, 'r') as myfile:
            # split des lignes --> récupération des infos sans '\n' en fin de ligne
            #  différent de .readlines() qui lui ne supprime pas les '\n'
            mypallines = myfile.read().splitlines()
            myfile.close()

            self.nb = int(mypallines[0])
            self.values = np.zeros(self.nb, dtype=np.float64)
            self.colors = np.zeros((self.nb, 4), dtype=int)

            for i in range(self.nb):
                self.values[i] = mypallines[i*4+1]
                self.colors[i, 0] = mypallines[i*4+2]
                self.colors[i, 1] = mypallines[i*4+3]
                self.colors[i, 2] = mypallines[i*4+4]
                self.colors[i, 3] = 255

        self.fill_segmentdata()

    def is_valid(self):
        """Vérification de la validité de la palette"""

        if self.nb < 2:
            return False

        if self.values[0] >= self.values[-1]:
            return False

        for i in range(1, self.nb):
            if self.values[i] <= self.values[i-1]:
                return False

        return True

    def savefile(self, *args):
        """Lecture de la palette sur base d'un fichier WOLF .pal"""
        if len(args) > 0:
            # s'il y a un argument on le prend tel quel
            fn = str(args[0])
        else:
            # ouverture d'une boîte de dialogue
            file = wx.FileDialog(None, "Choose .pal file", wildcard="pal (*.pal)|*.pal|all (*.*)|*.*", style=wx.FD_SAVE)
            if file.ShowModal() == wx.ID_CANCEL:
                return
            else:
                # récuparétaion du nom de fichier avec chemin d'accès
                fn = file.GetPath()

        self.filename = fn

        # lecture du contenu
        with open(self.filename, 'w') as myfile:
            # split des lignes --> récupération des infos sans '\n' en fin de ligne
            #  différent de .readlines() qui lui ne supprime pas les '\n'
            myfile.write(str(self.nb)+'\n')
            for i in range(self.nb):
                myfile.write(str(self.values[i])+'\n')
                myfile.write(str(self.colors[i, 0])+'\n')
                myfile.write(str(self.colors[i, 1])+'\n')
                myfile.write(str(self.colors[i, 2])+'\n')

    def isopop(self, array: ma.masked_array, nbnotnull: int = 99999):
        """Remplissage des valeurs de palette sur base d'une équirépartition de valeurs"""

        sortarray = array.flatten(order='F')

        idx_nan = np.where(np.isnan(sortarray))
        if idx_nan[0].size > 0:
            sortarray = np.delete(sortarray, idx_nan)
            nbnotnull -= idx_nan[0].size
            logging.warning('NaN values found in array - removed from palette')

        sortarray.sort(axis=-1)

        # valeurs min et max
        if nbnotnull == 0:
            self.values[0] = 0
            self.values[1:] = 1

        else:
            nbnotnull = min(nbnotnull, sortarray.shape[0])

            self.values[0] = sortarray[0]

            if (nbnotnull == 99999):
                self.values[-1] = sortarray[-1]
                nb = sortarray.count()
            else:
                self.values[-1] = sortarray[nbnotnull-1]
                nb = nbnotnull

            interv = int(nb / (self.nb-1))
            if interv == 0:
                self.values[:] = self.values[-1]
                self.values[0] = self.values[-1]-1.
            else:
                for cur in range(1, self.nb-1):
                    self.values[cur] = sortarray[cur * interv]

        self.fill_segmentdata()

    def defaultgray_minmax(self, array: ma.masked_array, nbnotnull=99999):
        """Remplissage des valeurs de palette sur base d'une équirépartition de valeurs"""

        self.nb = 2
        self.values = np.asarray([np.min(array), np.max(array)], dtype=np.float64)
        self.colors = np.asarray([[0, 0, 0, 255], [255, 255, 255, 255]], dtype=np.int32)
        self.colorsflt = np.asarray([[0., 0., 0., 1.], [1., 1., 1., 1.]], dtype=np.float64)

        self.fill_segmentdata()

    def defaultblue_minmax(self, array: ma.masked_array, nbnotnull=99999):
        """Remplissage des valeurs de palette sur base d'une équirépartition de valeurs"""

        self.nb = 2
        self.values = np.asarray([np.min(array), np.max(array)], dtype=np.float64)
        self.colors = np.asarray([[255, 255, 255, 255], [0, 0, 255, 255]], dtype=np.int32)
        self.colorsflt = self.colors.astype(float)/255.
        # self.colorsflt = np.asarray([[0., 0., 0., 1.], [1., 1., 1., 1.]], dtype=np.float64)

        self.fill_segmentdata()

    def defaultred_minmax(self, array: ma.masked_array, nbnotnull=99999):
        """Remplissage des valeurs de palette sur base d'une équirépartition de valeurs"""

        self.nb = 2
        self.values = np.asarray([np.min(array), np.max(array)], dtype=np.float64)
        self.colors = np.asarray([[255, 255, 255, 255], [255, 0, 0, 255]], dtype=np.int32)
        self.colorsflt = self.colors.astype(float)/255.
        # self.colorsflt = np.asarray([[0., 0., 0., 1.], [1., 1., 1., 1.]], dtype=np.float64)

        self.fill_segmentdata()

    def defaultblue(self):
        """Remplissage des valeurs de palette sur base d'une équirépartition de valeurs"""

        self.nb = 2
        self.values = np.asarray([0., 1.], dtype=np.float64)
        self.colors = np.asarray([[255, 255, 255, 255], [0, 0, 255, 255]], dtype=np.int32)
        self.colorsflt = self.colors.astype(float)/255.
        # self.colorsflt = np.asarray([[0., 0., 0., 1.], [1., 1., 1., 1.]], dtype=np.float64)

        self.fill_segmentdata()

    def defaultblue3(self):
        """Remplissage des valeurs de palette sur base d'une équirépartition de valeurs"""

        self.nb = 3
        self.values = np.asarray([0., 1., 10.], dtype=np.float64)
        self.colors = np.asarray([[255, 255, 255, 255], [50, 130, 246, 255], [0, 0, 255, 255]], dtype=np.int32)
        self.colorsflt = self.colors.astype(float)/255.

        self.fill_segmentdata()
