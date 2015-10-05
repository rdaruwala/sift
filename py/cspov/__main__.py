#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.py
~~~

PURPOSE


REFERENCES


REQUIRES


:author: R.K.Garcia <rayg@ssec.wisc.edu>
:copyright: 2014 by University of Wisconsin Regents, see AUTHORS for more details
:license: GPLv3, see LICENSE for more details
"""
__author__ = 'rayg'
__docformat__ = 'reStructuredText'


from vispy import app
try:
    app_object = app.use_app('pyqt4')
except Exception:
    app_object = app.use_app('pyside')
QtCore = app_object.backend_module.QtCore
QtGui = app_object.backend_module.QtGui

from cspov.control.layer_list import LayerStackListViewModel
from cspov.view.MapWidget import CspovMainMapCanvas
from cspov.view.LayerRep import NEShapefileLines, TiledGeolocatedImage
from cspov.model import Document
from cspov.view.SceneGraphManager import SceneGraphManager
from cspov.queue import TaskQueue, test_task, TASK_PROGRESS, TASK_DOING
from cspov.workspace import Workspace

from functools import partial

# this is generated with pyuic4 pov_main.ui >pov_main_ui.py
from cspov.ui.pov_main_ui import Ui_MainWindow

import os
import logging

LOG = logging.getLogger(__name__)
PROGRESS_BAR_MAX = 1000


def test_layers_from_directory(ws, doc, layer_tiff_glob, range_txt=None):
    """
    TIFF_GLOB='/Users/keoni/Data/CSPOV/2015_07_14_195/00?0/HS*_B03_*merc.tif' VERBOSITY=3 python -m cspov
    :param model:
    :param view:
    :param layer_tiff_glob:
    :return:
    """
    from glob import glob
    range = None
    if range_txt:
        import re
        range = tuple(map(float, re.findall(r'[\.0-9]+', range_txt)))
    for tif in glob(layer_tiff_glob):
        # doc.addFullGlobMercatorColormappedFloatImageLayer(tif, range=range)
        # uuid, info, overview_data = ws.import_image(tif)
        uuid, info, overview_data = doc.open_file(tif)
        LOG.info('loaded uuid {} from {}'.format(uuid, tif))
        yield uuid, info, overview_data


def test_layers(ws, doc, glob_pattern=None):
    if glob_pattern:
        return test_layers_from_directory(ws, doc, glob_pattern, os.environ.get('RANGE', None))
    LOG.warning("No image glob pattern provided")
    return []


class Main(QtGui.QMainWindow):
    def _init_add_file_dialog(self):
        pass
        # self._b_adds_files = UserAddsFileToDoc(self, self.ui.)

    def change_tool(self, name="pz_camera"):
        buttons = [self.ui.panZoomToolButton, self.ui.pointSelectButton, self.ui.regionSelectButton]
        names = [self.scene_manager.pz_camera.name, self.scene_manager.point_probe_camera.name, self.scene_manager.polygon_probe_camera.name]
        names = dict((name,value) for (value,name) in enumerate(names))
        dex = names[name]
        for q,b in enumerate(buttons):
            b.setDown(dex==q)
        self.scene_manager.change_camera(dex)

    def update_progress_bar(self, status_info, *args, **kwargs):
        active = status_info[0]
        LOG.warning('{0!r:s}'.format(status_info))
        val = active[TASK_PROGRESS]
        txt = active[TASK_DOING]
        self.ui.progressBar.setValue(int(val*PROGRESS_BAR_MAX))
        self.ui.progressText.setText(txt)
        #LOG.warning('progress bar updated to {}'.format(val))

    def update_frame_slider(self, frame_info):
        frame_index, frame_count, animating = frame_info[:3]
        self.ui.animationSlider.setRange(0, frame_count-1)
        self.ui.animationSlider.setValue(frame_index or 0)
        LOG.debug('did update animation slider {} {}'.format(frame_index, frame_count))
        self.ui.animPlayPause.setDown(animating)
        self.ui.animationSlider.update()

    def change_layer_colormap(self, nfo):
        uuid = nfo['uuid']
        mapname = nfo['colormap']
        self.scene_manager.set_colormap(mapname, uuid=uuid)

    def __init__(self, workspace_dir=None, glob_pattern=None, border_shapefile=None):
        super(Main, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # refer to objectName'd entities as self.ui.objectName

        self.queue = TaskQueue()
        self.ui.progressBar.setRange(0, PROGRESS_BAR_MAX)
        self.queue.didMakeProgress.connect(self.update_progress_bar)

        # create document
        self.workspace = Workspace(workspace_dir)
        self.document = doc = Document(self.workspace)
        self.scene_manager = SceneGraphManager(doc, self.workspace, self.queue, glob_pattern=glob_pattern, parent=self)
        self.ui.mainWidgets.addTab(self.scene_manager.main_canvas.native, 'Mercator')

        self.scene_manager.didChangeFrame.connect(self.update_frame_slider)
        self.ui.animPlayPause.clicked.connect(self.scene_manager.layer_set.toggle_animation)
        self.ui.animForward.clicked.connect(self.scene_manager.layer_set.next_frame)
        last_frame = partial(self.scene_manager.layer_set.next_frame, frame_number=-1)
        self.ui.animBack.clicked.connect(last_frame)
        # TODO: connect animation slider to frame number
        # TODO: connect step forward and step back buttons to frame number (.next_frame)

        for uuid, ds_info, full_data in test_layers(self.workspace, self.document, glob_pattern=glob_pattern):
            # this now fires off a document modification cascade resulting in a new layer going up
            pass

        # Interaction Setup
        self.setup_key_releases()
        self.scheduler = QtCore.QTimer(parent=self)
        self.scheduler.setInterval(200.0)
        # self.scheduler.timeout.connect(partial(self.scene_manager.image_list._timeout_slot, self.scheduler))
        self.scheduler.timeout.connect(partial(self.scene_manager.on_view_change, self.scheduler))
        def start_wrapper(timer, event):
            """Simple wrapper around a timers start method so we can accept but ignore the event provided
            """
            timer.start()
        self.scene_manager.main_canvas.events.draw.connect(partial(start_wrapper, self.scheduler))

        def update_probe_point(uuid, xy_pos):
            data_point = self.workspace.get_content_point(uuid, xy_pos)
            self.ui.cursorProbeText.setText("Point Probe: {:.03f}".format(data_point))
        self.scene_manager.newProbePoint.connect(update_probe_point)
        def update_probe_polygon(uuid, points):
            data_polygon = self.workspace.get_content_polygon(uuid, points)
            avg = data_polygon.mean()
            self.ui.cursorProbeText.setText("Polygon Probe: {:.03f}".format(avg))
            self.scene_manager.on_new_polygon(points)
        self.scene_manager.newProbePolygon.connect(update_probe_polygon)

        self.ui.mainWidgets.removeTab(0)
        self.ui.mainWidgets.removeTab(0)

        # convey action between document and layer list view
        self.behaviorLayersList = LayerStackListViewModel([self.ui.layerSet1Table, self.ui.layerSet2Table, self.ui.layerSet3Table, self.ui.layerSet4Table], doc)

        # self.queue.add('test', test_task(), 'test000')
        # self.ui.layers
        print(self.scene_manager.main_view.describe_tree(with_transform=True))
        self.document.docDidChangeEnhancement.connect(self.change_layer_colormap)

        self.ui.panZoomToolButton.clicked.connect(partial(self.change_tool, name=self.scene_manager.pz_camera.name))
        self.ui.pointSelectButton.clicked.connect(partial(self.change_tool, name=self.scene_manager.point_probe_camera.name))
        self.ui.regionSelectButton.clicked.connect(partial(self.change_tool, name=self.scene_manager.polygon_probe_camera.name))
        self.change_tool()

    def setup_key_releases(self):
        def cb_factory(required_key, cb):
            def tmp_cb(key, cb=cb):
                if key.text == required_key:
                    return cb()
            return tmp_cb

        self.scene_manager.main_canvas.events.key_release.connect(cb_factory("a", self.scene_manager.layer_set.toggle_animation))
        self.scene_manager.main_canvas.events.key_release.connect(cb_factory("n", self.scene_manager.layer_set.next_frame))
        self.scene_manager.main_canvas.events.key_release.connect(cb_factory("c", self.scene_manager.next_camera))

    def updateLayerList(self):
        # self.ui.layers.add
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run CSPOV")
    parser.add_argument("-w", "--workspace", default='.',
                        help="Specify workspace base directory")
    parser.add_argument("--border-shapefile", default=None,
                        help="Specify alternative coastline/border shapefile")
    parser.add_argument("--glob-pattern", default=os.environ.get("TIFF_GLOB", None),
                        help="Specify glob pattern for input images")
    parser.add_argument('-v', '--verbose', dest='verbosity', action="count", default=int(os.environ.get("VERBOSITY", 2)),
                        help='each occurrence increases verbosity 1 level through ERROR-WARNING-INFO-DEBUG (default INFO)')
    args = parser.parse_args()

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    level=levels[min(3, args.verbosity)]
    logging.basicConfig(level=level)
    # logging.getLogger('vispy').setLevel(level)

    app.create()
    # app = QApplication(sys.argv)
    window = Main(
        workspace_dir=args.workspace,
        glob_pattern=args.glob_pattern,
        border_shapefile=args.border_shapefile
    )
    window.show()
    print("running")
    # bring window to front
    window.raise_()
    app.run()

if __name__ == '__main__':
    import sys
    sys.exit(main())
