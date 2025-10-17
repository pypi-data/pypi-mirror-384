# -*- coding: utf-8 -*-
"""
Viewer TIFF 16 bits avec réglage d'étalement, zoom/pan
+ navigation dossier (←/→ et boutons)
+ modes: linéaire, gamma 0.5, gamma 2.0, sigmoide,
         log, inverse-log, exponentielle, racine √, racine ³,
         HE (global), CLAHE (local via scikit-image si dispo)
Toutes les courbes respectent les bornes min/max (percentiles).
Rafraîchissement immédiat sur toute interaction.
Affiche la colonne/ligne sous la souris.
Dépendances: AnyQt, numpy, tifffile
Optionnel: scikit-image (pour CLAHE)
"""
import sys
import numpy as np
import re
import tifffile as tiff

import os
from typing import List, Dict, Any
from AnyQt import QtWidgets, QtGui, QtCore
from scipy.ndimage import uniform_filter
# --- CLAHE optionnel via scikit-image ---
try:
    from skimage import exposure as sk_exposure
    HAS_SKIMAGE = True
except Exception:
    HAS_SKIMAGE = False
if "site-packages/Orange/widgets" in os.path.dirname(os.path.abspath(__file__)).replace("\\", "/"):
    from Orange.widgets.orangecontrib.IMG4IT.utils.reacalage_image import apply_transform_to_image_file
else:
    from orangecontrib.IMG4IT.utils.reacalage_image import apply_transform_to_image_file

def qimage_from_gray_uint8(arr_u8: np.ndarray) -> QtGui.QImage:
    """Convertit un ndarray uint8 (H, W) en QImage Grayscale8 sans copie."""
    if arr_u8.dtype != np.uint8 or arr_u8.ndim != 2:
        raise ValueError("qimage_from_gray_uint8 attend un array (H, W) en uint8.")
    if not arr_u8.flags["C_CONTIGUOUS"]:
        arr_u8 = np.ascontiguousarray(arr_u8)
    h, w = arr_u8.shape
    bytes_per_line = arr_u8.strides[0]
    qimg = QtGui.QImage(arr_u8.data, w, h, bytes_per_line,
                        QtGui.QImage.Format.Format_Grayscale8)
    qimg._arr_ref = arr_u8  # garder réf vivante
    return qimg


def hist_uint16(arr_u16: np.ndarray) -> np.ndarray:
    return np.bincount(arr_u16.ravel(), minlength=65536)


def percentile_from_hist(hist: np.ndarray, total_px: int, p: float) -> int:
    """Retourne une valeur 16 bits au percentile p en s'appuyant sur l'histogramme 65536 bins."""
    if p <= 0:
        return 0
    if p >= 100:
        return 65535
    target = total_px * (p / 100.0)
    cdf = np.cumsum(hist, dtype=np.int64)
    idx = int(np.searchsorted(cdf, target, side="left"))
    return int(np.clip(idx, 0, 65535))


# === HE & CLAHE sur t in [0,1] ===
def he_on_unit_float(t: np.ndarray, nbins: int = 256) -> np.ndarray:
    t = np.clip(t.astype(np.float32), 0.0, 1.0)
    h, bins = np.histogram(t, bins=int(max(2, nbins)), range=(0.0, 1.0))
    cdf = np.cumsum(h).astype(np.float32)
    if cdf[-1] <= 0:
        return t
    cdf /= cdf[-1]
    bin_centers = (bins[:-1] + bins[1:]) * 0.5
    y = np.interp(t.ravel(), bin_centers, cdf).reshape(t.shape).astype(np.float32)
    return y

def wallis_filter(t: np.ndarray, win_size: int,
                  mu_target: float = 50.0, sigma_target: float = 30.0) -> np.ndarray:
    """
    Apply the Wallis filter on a normalized image t ∈ [0,1].
    - win_size : local window size (odd recommended).
    - mu_target : target mean (in 0–255 scale).
    - sigma_target : target std (in 0–255 scale).
    Returns a float32 image in [0,1].
    """
    t = t.astype(np.float32)

    # Local mean and variance using uniform filter
    local_mean = uniform_filter(t, size=win_size, mode="reflect")
    local_mean_sq = uniform_filter(t * t, size=win_size, mode="reflect")
    local_var = np.maximum(local_mean_sq - local_mean * local_mean, 1e-6)
    local_std = np.sqrt(local_var, dtype=np.float32)

    # Wallis transform
    mu_c = mu_target / 255.0
    sigma_c = sigma_target / 255.0
    y = (t - local_mean) * (sigma_c / (local_std + 1e-6)) + mu_c

    # Ensure result stays within [0,1]
    y = np.clip(y, 0.0, 1.0).astype(np.float32)
    return y




def clahe_on_unit_float(t: np.ndarray, clip_limit: float = 0.01, nbins: int = 256) -> np.ndarray:
    t = np.clip(t.astype(np.float32), 0.0, 1.0)
    if HAS_SKIMAGE:
        y = sk_exposure.equalize_adapthist(t, clip_limit=float(max(1e-6, clip_limit)), nbins=int(max(2, nbins)))
        return y.astype(np.float32, copy=False)
    # fallback: HE global
    return he_on_unit_float(t, nbins=nbins)


class ImageView(QtWidgets.QGraphicsView):
    """Widget avec zoom + pan à la souris + émission des coords souris."""
    mouseMoved = QtCore.Signal(int, int)  # (col, row)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHints(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.viewport().setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._img_w = 0
        self._img_h = 0
        # Curseur en croix
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.viewport().installEventFilter(self)

    # sinon on rebscule a la main
    def eventFilter(self, obj, ev):
        if obj is self.viewport() and ev.type() == QtCore.QEvent.CursorChange:
            if self.viewport().cursor().shape() != QtCore.Qt.CrossCursor:
                QtCore.QTimer.singleShot(0, lambda: self.viewport().setCursor(QtCore.Qt.CrossCursor))
                return True
        return super().eventFilter(obj, ev)

    def set_image_size(self, w: int, h: int):
        self._img_w = int(max(0, w))
        self._img_h = int(max(0, h))

    def wheelEvent(self, event: QtGui.QWheelEvent):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        f = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.scale(f, f)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        # Coordonnées scène sous la souris
        sp = self.mapToScene(event.pos())#.toPoint())
        x = int(np.floor(sp.x()))
        y = int(np.floor(sp.y()))
        # Borne dans l'image
        if 0 <= x < self._img_w and 0 <= y < self._img_h:
            self.mouseMoved.emit(x, y)
        else:
            # Hors image -> on émet -1 pour signaler "n/a"
            self.mouseMoved.emit(-1, -1)
        super().mouseMoveEvent(event)


class Tiff16Viewer(QtWidgets.QWidget):
    def __init__(self, input_path, parent=None):
        super().__init__(parent)

        # --- Résolution du dossier et de la liste d'images ---
        self.files = []
        self.idx = 0
        self._resolve_inputs(input_path)

        # --- État traitement ---
        self.arr16 = None
        self.h = self.w = 0
        self.hist = None
        self.total_px = 0
        self.min_val = 0
        self.max_val = 0
        self._last_img8 = None  # ndarray uint8 (H, W) de la dernière vue affichée

        # --- Vue graphique (zoom/pan) ---
        self.scene = QtWidgets.QGraphicsScene()
        self.view = ImageView()
        self.view.setScene(self.scene)
        self.pixmap_item = QtWidgets.QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        # --- Bandeau nom de fichier + navigation ---
        self.name_label = QtWidgets.QLabel("--")
        self.name_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)


        nav = QtWidgets.QHBoxLayout()
        nav.addStretch(1)
        nav.addWidget(self.name_label)

        # --- Coordonnées souris (colonnes / lignes) ---
        self.col_edit = QtWidgets.QLineEdit()
        self.col_edit.setReadOnly(True)
        self.col_edit.setFixedWidth(90)
        self.col_edit.setPlaceholderText("Colonne")
        self.row_edit = QtWidgets.QLineEdit()
        self.row_edit.setReadOnly(True)
        self.row_edit.setFixedWidth(90)
        self.row_edit.setPlaceholderText("Ligne")

        # valeur de m intensité
        self.val_edit = QtWidgets.QLineEdit()
        self.val_edit.setReadOnly(True)
        self.val_edit.setFixedWidth(140)
        self.val_edit.setPlaceholderText("Valeur 16b → 8b")

        coords = QtWidgets.QHBoxLayout()
        coords.addWidget(QtWidgets.QLabel("Col:"))
        coords.addWidget(self.col_edit)
        coords.addSpacing(8)
        coords.addWidget(QtWidgets.QLabel("Ligne:"))
        coords.addWidget(self.row_edit)
        coords.addSpacing(8)
        coords.addWidget(QtWidgets.QLabel("Valeur:"))
        coords.addWidget(self.val_edit)
        coords.addStretch(1)
        # --- Contrôles percentiles ---
        self.low_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.high_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        for s in (self.low_slider, self.high_slider):
            s.setRange(0, 100)
            s.setTickInterval(5)
            s.setSingleStep(1)
            s.setTracking(True)  # rafraîchit pendant le drag
        self.low_slider.setValue(2)
        self.high_slider.setValue(98)

        self.low_spin = QtWidgets.QSpinBox(); self.low_spin.setRange(0, 100); self.low_spin.setSuffix(" %")
        self.high_spin = QtWidgets.QSpinBox(); self.high_spin.setRange(0, 100); self.high_spin.setSuffix(" %")
        self.low_spin.setValue(self.low_slider.value())
        self.high_spin.setValue(self.high_slider.value())

        # --- Boutons d'étendue ---
        self.btn_auto = QtWidgets.QPushButton("Auto (2–98%)")
        self.btn_full = QtWidgets.QPushButton("Plein écart (min–max)")
        self.btn_reset = QtWidgets.QPushButton("Réinitialiser vue")

        # --- Boutons d'augmentation de contraste ---
        # existants
        self.btn_lin = QtWidgets.QPushButton("Lineaire")
        self.btn_gam05 = QtWidgets.QPushButton("Gamma 0.5")
        self.btn_gam20 = QtWidgets.QPushButton("Gamma 2.0")
        self.btn_sig = QtWidgets.QPushButton("Sigmoide")
        # nouveaux
        self.btn_log = QtWidgets.QPushButton("Log")
        self.btn_invlog = QtWidgets.QPushButton("Inverse-Log")
        self.btn_exp = QtWidgets.QPushButton("Exponentielle")
        self.btn_sqrt = QtWidgets.QPushButton("Racine carree")
        self.btn_cbrt = QtWidgets.QPushButton("Racine cubique")
        self.btn_he = QtWidgets.QPushButton("HE (global)")
        self.btn_clahe = QtWidgets.QPushButton("CLAHE")
        self.wallis_win_spin = QtWidgets.QSpinBox()
        self.wallis_win_spin.setRange(3, 101)
        self.wallis_win_spin.setSingleStep(2)
        self.wallis_win_spin.setValue(15)
        self.wallis_win_spin.setToolTip("Window size for Wallis filter (odd)")
        self.wallis_win_spin.valueChanged.connect(self.update_view)

        # Réglages HE / CLAHE
        self.he_bins_spin = QtWidgets.QSpinBox()
        self.he_bins_spin.setRange(16, 4096)
        self.he_bins_spin.setSingleStep(16)
        self.he_bins_spin.setValue(256)
        self.he_bins_spin.setToolTip("Nombre de bins pour HE (global)")
        self.clahe_clip_spin = QtWidgets.QDoubleSpinBox()
        self.clahe_clip_spin.setRange(0.001, 0.100)
        self.clahe_clip_spin.setSingleStep(0.001)
        self.clahe_clip_spin.setDecimals(3)
        self.clahe_clip_spin.setValue(0.010)
        self.clahe_clip_spin.setToolTip("Clip limit pour CLAHE")

        # Wallis target mean (0..255) et target std (0..255)
        self.wallis_mu_spin = QtWidgets.QSpinBox()
        self.wallis_mu_spin.setRange(0, 255)
        self.wallis_mu_spin.setValue(127)
        self.wallis_mu_spin.setToolTip("Wallis target mean (0..255)")

        self.wallis_sigma_spin = QtWidgets.QSpinBox()
        self.wallis_sigma_spin.setRange(0, 255)
        self.wallis_sigma_spin.setValue(35)
        self.wallis_sigma_spin.setToolTip("Wallis target std (0..255)")

        # Rafraîchissement immédiat
        self.wallis_mu_spin.valueChanged.connect(self.update_view)
        self.wallis_sigma_spin.valueChanged.connect(self.update_view)
        # État courant de la courbe
        # modes: linear, gamma05, gamma20, sigmoid, log, invlog, exp, sqrt, cbrt, he, clahe
        self.contrast_mode = "linear"

        # --- Layouts ---
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Percentile bas"), 0, 0)
        grid.addWidget(self.low_slider, 0, 1)
        grid.addWidget(self.low_spin, 0, 2)
        grid.addWidget(QtWidgets.QLabel("Percentile haut"), 1, 0)
        grid.addWidget(self.high_slider, 1, 1)
        grid.addWidget(self.high_spin, 1, 2)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.btn_auto)
        btns.addWidget(self.btn_full)
        btns.addWidget(self.btn_reset)
        btns.addStretch(1)

        contrast_btns1 = QtWidgets.QHBoxLayout()
        contrast_btns1.addWidget(QtWidgets.QLabel("Courbe contraste :"))
        for b in (self.btn_lin, self.btn_gam05, self.btn_gam20, self.btn_sig):
            contrast_btns1.addWidget(b)
        contrast_btns1.addStretch(1)

        contrast_btns2 = QtWidgets.QHBoxLayout()
        for b in (self.btn_log, self.btn_invlog, self.btn_exp, self.btn_sqrt, self.btn_cbrt, self.btn_he, self.btn_clahe):
            contrast_btns2.addWidget(b)
        self.btn_wallis = QtWidgets.QPushButton("Wallis")
        self.btn_wallis.clicked.connect(lambda: self.set_contrast_mode("wallis"))
        contrast_btns2.addWidget(self.btn_wallis)
        contrast_btns2.addStretch(1)


        params_row = QtWidgets.QHBoxLayout()
        params_row.addWidget(QtWidgets.QLabel("HE nbins:"))
        params_row.addWidget(self.he_bins_spin)
        params_row.addSpacing(12)
        params_row.addWidget(QtWidgets.QLabel("CLAHE clip_limit:"))
        params_row.addWidget(self.clahe_clip_spin)

        params_row.addSpacing(12)
        params_row.addWidget(QtWidgets.QLabel("Wallis Windows size :"))
        params_row.addWidget(self.wallis_win_spin)

        params_row.addSpacing(12)
        params_row.addWidget(QtWidgets.QLabel("Wallis target mean:"))
        params_row.addWidget(self.wallis_mu_spin)
        params_row.addSpacing(6)
        params_row.addWidget(QtWidgets.QLabel("Wallis target std dev:"))
        params_row.addWidget(self.wallis_sigma_spin)


        params_row.addStretch(1)
        # --- Panneau d'infos (lecture seule) ---
        self.info_edit = QtWidgets.QLineEdit()
        self.info_edit.setReadOnly(True)
        self.info_edit.setPlaceholderText("Infos : min (intensité), mode, HE bins, CLAHE clip")

        v = QtWidgets.QVBoxLayout(self)
        v.addLayout(nav)
        v.addWidget(self.view, stretch=1)
        v.addLayout(coords)           # <<--- coordonnées souris
        v.addLayout(grid)
        v.addLayout(btns)
        v.addLayout(contrast_btns1)
        v.addLayout(contrast_btns2)
        v.addLayout(params_row)
        v.addWidget(self.info_edit)

        # --- Connexions (rafraîchissement immédiat) ---
        self.low_slider.valueChanged.connect(self._on_low_slider)
        self.high_slider.valueChanged.connect(self._on_high_slider)
        self.low_spin.valueChanged.connect(self._on_low_spin)
        self.high_spin.valueChanged.connect(self._on_high_spin)

        self.btn_auto.clicked.connect(self.apply_auto)
        self.btn_full.clicked.connect(self.apply_full)
        self.btn_reset.clicked.connect(self.reset_view)

        # modes existants
        self.btn_lin.clicked.connect(lambda: self.set_contrast_mode("linear"))
        self.btn_gam05.clicked.connect(lambda: self.set_contrast_mode("gamma05"))
        self.btn_gam20.clicked.connect(lambda: self.set_contrast_mode("gamma20"))
        self.btn_sig.clicked.connect(lambda: self.set_contrast_mode("sigmoid"))

        # nouveaux modes
        self.btn_log.clicked.connect(lambda: self.set_contrast_mode("log"))
        self.btn_invlog.clicked.connect(lambda: self.set_contrast_mode("invlog"))
        self.btn_exp.clicked.connect(lambda: self.set_contrast_mode("exp"))
        self.btn_sqrt.clicked.connect(lambda: self.set_contrast_mode("sqrt"))
        self.btn_cbrt.clicked.connect(lambda: self.set_contrast_mode("cbrt"))
        self.btn_he.clicked.connect(lambda: self.set_contrast_mode("he"))
        self.btn_clahe.clicked.connect(lambda: self.set_contrast_mode("clahe"))

        # réglages HE/CLAHE
        self.he_bins_spin.valueChanged.connect(self.update_view)
        self.clahe_clip_spin.valueChanged.connect(self.update_view)



        # coords souris
        self.view.mouseMoved.connect(self._on_mouse_moved)

        # Charge la première image
        self._load_current_image()

    def _human_mode_name(self) -> str:
        mapping = {
            "linear": "Lineaire",
            "gamma05": "Gamma 0.5",
            "gamma20": "Gamma 2.0",
            "sigmoid": "Sigmoide",
            "log": "Logarithmique",
            "invlog": "Inverse-Log",
            "exp": "Exponentielle",
            "sqrt": "Racine carree",
            "cbrt": "Racine cubique",
            "he": "HE (global)",
            "clahe": "CLAHE",
            "wallis": "Wallis",
        }
        return mapping.get(self.contrast_mode, self.contrast_mode)

    def _update_info_panel(self, low_val: int, high_val: int):
        # low_val = borne min (intensité 16 bits) actuellement utilisée (depuis les percentiles)
        mode_human = self._human_mode_name()
        he_bins = int(self.he_bins_spin.value())
        clahe_clip = float(self.clahe_clip_spin.value())
        extra = []
        if self.contrast_mode == "he":
            extra.append(f"    HE bins = {he_bins}")
        if self.contrast_mode == "clahe":
            extra.append(f"    CLAHE clip = {clahe_clip:.3f}")
        if self.contrast_mode == "wallis":
            extra.append(
                f"Wallis average={int(self.wallis_mu_spin.value())}    |    standard deviation={int(self.wallis_sigma_spin.value())}    |    win_size={int(self.wallis_win_spin.value())}")
        extra_str = ("    | " + " | ".join(extra)) if extra else ""

        # Affiche au minimum la borne min (intensité). On ajoute aussi la borne max : utile pour contrôle visuel.
        text = (f"Transform    |    "
            f"Min (I16) = {low_val}"
            f"    |    Max (I16) = {high_val}"
            f"    |    Mode = {mode_human}"
            f"{extra_str}"
        )
        self.info_edit.setText(text)

    # ---------- Gestion des entrées ----------
    def _resolve_inputs(self, input_path):
        path = os.path.abspath(input_path)
        if os.path.isdir(path):
            folder = path
            start_file = None
        else:
            folder = os.path.dirname(path) if os.path.dirname(path) else "."
            start_file = os.path.basename(path)

        exts = {".tif", ".tiff"}
        files = [f for f in os.listdir(folder)
                 if os.path.splitext(f)[1].lower() in exts]
        files.sort(key=lambda x: x.lower())

        if not files:
            QtWidgets.QMessageBox.critical(None, "Erreur", f"Aucune image .tif/.tiff dans :\n{folder}")
            sys.exit(1)

        self.files = [os.path.join(folder, f) for f in files]

        if start_file:
            try:
                self.idx = files.index(start_file)
            except ValueError:
                self.idx = 0
        else:
            self.idx = 0

    # ---------- Chargement d'image ----------
    def _load_current_image(self):
        path = self.files[self.idx]
        self._load_image_from_path(path)
        self.view.resetTransform()  # zoom 1:1
        self.update_view()
        self._update_name_label()

    def _load_image_from_path(self, path):
        arr = tiff.imread(path)
        if arr.ndim == 3:
            arr = arr[..., 0]
        if arr.dtype != np.uint16:
            arr = arr.astype(np.uint16, copy=False)
        self.arr16 = np.ascontiguousarray(arr)
        self.h, self.w = self.arr16.shape

        # Histogramme/stat
        self.hist = hist_uint16(self.arr16)
        self.total_px = int(self.arr16.size)
        self.min_val = int(self.arr16.min())
        self.max_val = int(self.arr16.max())

        # Ajuster la scène à la nouvelle taille
        self.scene.setSceneRect(0, 0, self.w, self.h)
        self.view.set_image_size(self.w, self.h)  # <<--- pour le suivi souris

    def _update_name_label(self):
        base = os.path.basename(self.files[self.idx])
        self.name_label.setText(f"{base}")


    # ---------- Contraste ----------
    def set_contrast_mode(self, mode: str):
        self.contrast_mode = mode
        self.update_view()

    def compute_low_high_values(self):
        low_p, high_p = self.low_slider.value(), self.high_slider.value()
        if high_p <= low_p:
            high_p = min(low_p + 1, 100)
            for w, val in ((self.high_slider, high_p), (self.high_spin, high_p)):
                w.blockSignals(True); w.setValue(val); w.blockSignals(False)
        low_val = percentile_from_hist(self.hist, self.total_px, low_p)
        high_val = percentile_from_hist(self.hist, self.total_px, high_p)
        if high_val <= low_val:
            high_val = min(low_val + 1, 65535)
        return low_val, high_val

    @staticmethod
    def apply_curve_pointwise(t: np.ndarray, mode: str) -> np.ndarray:
        # t ∈ [0,1] en float32 — toutes les courbes partent de cette normalisation
        if mode == "linear":
            y = t
        elif mode == "gamma05":
            y = np.power(t, 0.5, dtype=np.float32)
        elif mode == "gamma20":
            y = np.power(t, 2.0, dtype=np.float32)
        elif mode == "sigmoid":
            gain = 10.0
            y = 1.0 / (1.0 + np.exp(-gain * (t - 0.5)))
            y = (y - y.min()) / max(1e-12, (y.max() - y.min()))
        elif mode == "log":
            c = 100.0
            y = np.log1p(c * t) / np.log1p(c)
        elif mode == "invlog":
            c = 4.0
            y = (np.expm1(c * t) / np.expm1(c)).astype(np.float32)
        elif mode == "exp":
            k = 0.7
            y = np.power(t, k, dtype=np.float32)
        elif mode == "sqrt":
            y = np.sqrt(t, dtype=np.float32)
        elif mode == "cbrt":
            y = np.power(t, 1.0 / 3.0, dtype=np.float32)
        elif mode == "wallis":
            # default window size if no UI is connected
            y = wallis_filter(t, win_size=15)
        else:
            y = t
        return np.clip(y, 0.0, 1.0).astype(np.float32)

    def stretch_to_8bit(self, arr16: np.ndarray, lv: int, hv: int) -> np.ndarray:
        # Normalisation stricte par bornes min/max choisies (percentiles) → T dans [0,1]
        rng = float(max(1, hv - lv))
        t = (arr16.astype(np.int32) - lv) / rng
        t = np.clip(t, 0.0, 1.0).astype(np.float32)

        mode = self.contrast_mode
        if mode == "he":
            y = he_on_unit_float(t, nbins=int(self.he_bins_spin.value()))
        elif mode == "clahe":
            y = clahe_on_unit_float(t, clip_limit=float(self.clahe_clip_spin.value()),
                                    nbins=int(self.he_bins_spin.value()))
        elif mode == "wallis":
            win_size = int(self.wallis_win_spin.value()) if hasattr(self, "wallis_win_spin") else 15
            mu_t = float(self.wallis_mu_spin.value()) if hasattr(self, "wallis_mu_spin") else 127.0
            sigma_t = float(self.wallis_sigma_spin.value()) if hasattr(self, "wallis_sigma_spin") else 35.0
            y = wallis_filter(t, win_size=win_size, mu_target=mu_t, sigma_target=sigma_t)
        else:
            y = self.apply_curve_pointwise(t, mode)

        out = np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)
        return out

    # ---------- Rendu ----------
    def update_view(self):
        low_val, high_val = self.compute_low_high_values()
        img8 = self.stretch_to_8bit(self.arr16, low_val, high_val)
        self._last_img8 = img8
        qimg = qimage_from_gray_uint8(img8)
        self.pixmap_item.setPixmap(QtGui.QPixmap.fromImage(qimg))

        extra = ""
        if self.contrast_mode == "clahe" and not HAS_SKIMAGE:
            extra = " (CLAHE indisponible → HE)"
        title = (
            f"TIFF 16 bits – [{low_val} .. {high_val}] – {self.w}x{self.h} – "
            f"Mode: {self.contrast_mode}{extra} – HE bins={self.he_bins_spin.value()} – CLAHE clip={self.clahe_clip_spin.value():.3f}"
        )
        self.setWindowTitle(title)
        self._update_info_panel(low_val, high_val)

    # ---------- Slots UI (rafraîchissement immédiat) ----------
    def _on_low_slider(self, val):
        self.low_spin.blockSignals(True)
        self.low_spin.setValue(val)
        self.low_spin.blockSignals(False)
        self.update_view()

    def _on_high_slider(self, val):
        if val <= self.low_slider.value():
            val = min(self.low_slider.value() + 1, 100)
            self.high_slider.blockSignals(True)
            self.high_slider.setValue(val)
            self.high_slider.blockSignals(False)
        self.high_spin.blockSignals(True)
        self.high_spin.setValue(val)
        self.high_spin.blockSignals(False)
        self.update_view()

    def _on_low_spin(self, val):
        self.low_slider.blockSignals(True)
        self.low_slider.setValue(val)
        self.low_slider.blockSignals(False)
        self.update_view()

    def _on_high_spin(self, val):
        if val <= self.low_spin.value():
            val = min(self.low_spin.value() + 1, 100)
            self.high_spin.blockSignals(True)
            self.high_spin.setValue(val)
            self.high_spin.blockSignals(False)
        self.high_slider.blockSignals(True)
        self.high_slider.setValue(val)
        self.high_slider.blockSignals(False)
        self.update_view()

    def _on_mouse_moved(self, col: int, row: int):
        if col < 0 or row < 0:
            self.col_edit.setText("")
            self.row_edit.setText("")
        else:
            self.col_edit.setText(str(col))
            self.row_edit.setText(str(row))
        # Valeur brute 16 bits
        try:
            v16 = int(self.arr16[row, col])
        except Exception:
            v16 = None

        # Valeur affichée 8 bits (après étalement/courbe)
        v8 = None
        if self._last_img8 is not None:
            try:
                v8 = int(self._last_img8[row, col])
            except Exception:
                v8 = None

        if v16 is None:
            self.val_edit.setText("")
        else:
            # Format "65535 → 240" (par ex.)
            self.val_edit.setText(f"{v16}" + (f" \u2192 {v8}" if v8 is not None else ""))

    def apply_auto(self):
        self.low_slider.setValue(2)
        self.high_slider.setValue(98)
        self.update_view()

    def apply_full(self):
        self.low_slider.setValue(0)
        self.high_slider.setValue(100)
        self.update_view()

    def reset_view(self):
        self.view.resetTransform()
        self.update_view()



def view_tiff_qt(input_path, parent=None):
    app = QtWidgets.QApplication.instance()
    owns_app = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv[:1])
        owns_app = True

    w = Tiff16Viewer(input_path, parent=parent)
    w.resize(1200, 950)
    w.show()

    if owns_app:
        # Mode script autonome
        sys.exit(app.exec())

    # Mode "intégré" (ex. depuis Orange) : on rend la fenêtre au caller
    return w

def _normalize_mode_name(s: str) -> str:
    """Mappe un libellé humain -> code interne du viewer."""
    s0 = (s or "").strip().lower()
    # enlever accents légers pour la correspondance
    s0 = (s0
          .replace("é", "e").replace("è", "e").replace("ê", "e")
          .replace("ï", "i").replace("î", "i")
          .replace("ô", "o").replace("ö", "o").replace("à", "a")
          .replace("ç", "c"))
    s0 = s0.replace("  ", " ")

    aliases = {
        "lineaire": "linear",
        "linear": "linear",
        "gamma 0.5": "gamma05",
        "gamma0.5": "gamma05",
        "gamma 2.0": "gamma20",
        "gamma2.0": "gamma20",
        "sigmoide": "sigmoid",
        "sigmoid": "sigmoid",
        "logarithmique": "log",
        "log": "log",
        "inverse-log": "invlog",
        "inverse log": "invlog",
        "exponentielle": "exp",
        "exp": "exp",
        "racine carree": "sqrt",
        "sqrt": "sqrt",
        "racine cubique": "cbrt",
        "cbrt": "cbrt",
        "he (global)": "he",
        "he": "he",
        "clahe": "clahe",
        "wallis": "wallis",
    }
    return aliases.get(s0, s0)

def _parse_transform_spec(spec: str):
    """
    Exemples acceptés (espaces insensibles) :
      Transform | Min (I16) = 36727 | Max (I16) = 61597 | Mode = Lineaire
      ... | Mode = HE (global) | HE bins = 144
      ... | Mode = CLAHE | CLAHE clip = 0.024
    """
    if not isinstance(spec, str):
        raise ValueError("transform_spec doit être une chaîne.")

    # Min/Max
    m_min = re.search(r"Min\s*\(I16\)\s*=\s*(\d+)", spec, re.I)
    m_max = re.search(r"Max\s*\(I16\)\s*=\s*(\d+)", spec, re.I)
    m_mode = re.search(r"Mode\s*=\s*([^\|]+)", spec, re.I)

    if not (m_min and m_max and m_mode):
        raise ValueError("Chaîne invalide : impossible d'extraire Min/Max/Mode.")

    low_val = int(m_min.group(1))
    high_val = int(m_max.group(1))
    mode_human = m_mode.group(1).strip()
    mode = _normalize_mode_name(mode_human)

    # Paramètres optionnels
    he_bins = None
    m_bins = re.search(r"HE\s*bins\s*=\s*(\d+)", spec, re.I)
    if m_bins:
        he_bins = int(m_bins.group(1))

    clahe_clip = None
    m_clip = re.search(r"CLAHE\s*clip\s*=\s*([0-9]*\.?[0-9]+)", spec, re.I)
    if m_clip:
        clahe_clip = float(m_clip.group(1))

    # bornes sécurisées
    low_val = int(max(0, min(65535, low_val)))
    high_val = int(max(low_val + 1, min(65535, high_val)))

    # return {
    #     "low_val": low_val,
    #     "high_val": high_val,
    #     "mode_human": mode_human,
    #     "mode": mode,
    #     "he_bins": he_bins,
    #     "clahe_clip": clahe_clip,
    # }
    # --- Wallis (anglais et français acceptés) ---
    m_mu    = re.search(r"(?:wallis\s*)?(?:average|mean|mu|moyenne)\s*=\s*([0-9]+(?:\.[0-9]+)?)", spec, re.I)
    m_sigma = re.search(r"(?:wallis\s*)?(?:standard\s*deviation|std|sigma|ecart\s*type)\s*=\s*([0-9]+(?:\.[0-9]+)?)", spec, re.I)
    m_win   = re.search(r"(?:wallis\s*)?(?:win(?:_)?size|window(?:_)?size|fenetre|taille\s*fenetre)\s*=\s*(\d+)", spec, re.I)

    wallis_mu    = float(m_mu.group(1))    if m_mu    else None
    wallis_sigma = float(m_sigma.group(1)) if m_sigma else None
    wallis_win   = int(m_win.group(1))     if m_win   else None

    return {
        "low_val": low_val,
        "high_val": high_val,
        "mode_human": mode_human,
        "mode": mode,
        "he_bins": he_bins,
        "clahe_clip": clahe_clip,
        "wallis_mu": wallis_mu,
        "wallis_sigma": wallis_sigma,
        "wallis_win": wallis_win
    }


def _parse_crop_spec(spec: str):
    """
    Exemples acceptés (espaces optionnels, insensible à la casse) :
      "Crop | line = 0 | col = 12 | delta_line = 50 | delta_col = 22"
      "crop|line=10|col=20|delta_line=100|delta_col=80"
    line/col : indices (0-based) ligne/colonne du coin supérieur gauche du crop
    delta_line/delta_col : hauteur/largeur du crop (en pixels)
    """
    if not isinstance(spec, str):
        raise ValueError("crop_spec must be a string.")

    def get_int(pattern):
        m = re.search(pattern, spec, flags=re.I)
        if not m:
            return None
        return int(m.group(1))

    line = get_int(r"\bline\s*=\s*(-?\d+)")
    col = get_int(r"\bcol\s*=\s*(-?\d+)")
    dline = get_int(r"\bdelta[_\s]*line\s*=\s*(\d+)")
    dcol = get_int(r"\bdelta[_\s]*col\s*=\s*(\d+)")

    if line is None or col is None or dline is None or dcol is None:
        raise ValueError(
            "Invalid crop spec. Expected: 'Crop | line = <int> | col = <int> | "
            "delta_line = <int> | delta_col = <int>'"
        )
    if dline <= 0 or dcol <= 0:
        raise ValueError("delta_line and delta_col must be positive integers.")

    return line, col, dline, dcol


def crop_tiff_by_spec(src_path: str, dst_path: str, crop_spec: str):
    """
    Croppe un TIFF selon 'crop_spec' en conservant le format d'entrée (bit depth & canaux).

    Cas gérés :
      - (H, W) uint16  -> sortie (Hc, Wc) uint16           (mono 16-bit)
      - (H, W) uint8   -> sortie (Hc, Wc) uint8            (mono 8-bit)
      - (H, W, 3) uint8 -> sortie (Hc, Wc, 3) uint8        (RGB 8-bit)
      - (H, W, 4) uint8 -> sortie (Hc, Wc, 4) uint8        (RGBA 8-bit)

    Si l'image a d'autres formes/dtypes, lève ValueError.

    Retourne un dict avec la zone effectivement croppée (bornée).
    """
    # Lire l'image
    arr = tiff.imread(src_path)

    # Normaliser certains cas courants : si multi-canaux en 3D
    if arr.ndim == 2:
        # mono 8-bit ou 16-bit
        if arr.dtype == np.uint8:
            fmt = ("mono", np.uint8)
        elif arr.dtype == np.uint16:
            fmt = ("mono16", np.uint16)
        else:
            raise ValueError(f"Unsupported dtype for 2D image: {arr.dtype}")
    elif arr.ndim == 3:
        H, W, C = arr.shape
        if arr.dtype == np.uint8 and C in (3, 4):
            fmt = ("rgb" if C == 3 else "rgba", np.uint8)
        elif arr.dtype == np.uint8 and C == 1:
            # parfois stocké en (H,W,1) -> aplatissement en mono
            arr = arr[..., 0]
            fmt = ("mono", np.uint8)
        else:
            raise ValueError(f"Unsupported 3D image shape/dtype: {arr.shape}, {arr.dtype}")
    else:
        raise ValueError(f"Unsupported image ndim: {arr.ndim}")

    H, W = arr.shape[:2]

    # Parser la spec
    line, col, dline, dcol = _parse_crop_spec(crop_spec)

    # Zone demandée (y0:y1, x0:x1)
    y0 = max(0, line)
    x0 = max(0, col)
    y1 = min(H, y0 + dline)
    x1 = min(W, x0 + dcol)

    if y1 <= y0 or x1 <= x0:
        raise ValueError(
            f"Crop is empty after clamping to image bounds. "
            f"Requested line={line}, col={col}, dline={dline}, dcol={dcol}; "
            f"Image size = {H}x{W}."
        )

    # Extraire la ROI (contiguë)
    roi = arr[y0:y1, x0:x1, ...]
    roi = np.ascontiguousarray(roi)

    # Écriture avec photometric adéquat
    photometric = None
    extrasamples = None

    if fmt[0] == "mono16":
        photometric = "minisblack"
        # dtype déjà uint16
    elif fmt[0] == "mono":
        photometric = "minisblack"
        # dtype déjà uint8
    elif fmt[0] == "rgb":
        photometric = "rgb"
        # rien à ajouter
    elif fmt[0] == "rgba":
        photometric = "rgb"
        # indiquer un canal alpha non associé (optionnel, tifffile gère souvent sans)
        # extrasamples = 'unassoc'  # ou ['unassoc'] selon tifffile; souvent pas nécessaire
    else:
        raise RuntimeError("Unexpected format state.")

    # Écrire
    # tifffile choisit souvent correctement, mais on force photometric pour être explicite.
    if extrasamples is not None:
        tiff.imwrite(dst_path, roi, photometric=photometric, extrasamples=extrasamples)
    else:
        tiff.imwrite(dst_path, roi, photometric=photometric)

    return {
        "src": src_path,
        "dst": dst_path,
        "input_shape": tuple(arr.shape) if arr is not None else None,
        "output_shape": tuple(roi.shape),
        "dtype": str(roi.dtype),
        "crop_requested": {"line": line, "col": col, "delta_line": dline, "delta_col": dcol},
        "crop_effective": {"y0": int(y0), "x0": int(x0), "y1": int(y1), "x1": int(x1)},
    }

def _which_op(spec: str) -> str:
    """
    Retourne 'transform' ou 'crop' d'après le début de la chaîne (insensible à la casse/espaces).
    Lève ValueError si non reconnu.
    """
    if not isinstance(spec, str) or not spec.strip():
        raise ValueError("Operation spec must be a non-empty string.")
    head = spec.strip().split("|", 1)[0].strip().lower()
    # tolère 'transform' / 'transfrom' (typo fréquente) / 'crop'
    if re.match(r"^transf(?:or|ro)?m", head):  # accepte transform / transfrom
        return "transform"
    if head.startswith("crop"):
        return "crop"
    raise ValueError(f"Unknown operation type in spec header: '{head}'. Expected 'Transform' or 'Crop'.")

def _is_Rt_spec(spec: str) -> bool:
    """Retourne True si spec contient une matrice R et un vecteur t."""
    if not isinstance(spec, str):
        return False
    return bool(re.search(r"R\s*=\s*\[\[.*?\]\].*t\s*=\s*\[.*?\]", spec, flags=re.I | re.S))


def process_tiff_spec(src_path: str, dst_path: str, spec: str,
                      default_he_bins: int = 256, default_clahe_clip: float = 0.01):
    """
    Détecte automatiquement l'opération à partir de 'spec' et exécute :
      - Transform ...  -> transform_tiff16_to_tiff8(...)
      - Crop ...       -> crop_tiff_by_spec(...)

    Arguments:
      - src_path : chemin du TIFF d'entrée
      - dst_path : chemin du TIFF de sortie
      - spec     : chaîne de description ("Transform | ..." OU "Crop | ...")
      - default_he_bins / default_clahe_clip : valeurs par défaut pour Transform (HE/CLAHE)

    Retourne un dict récapitulatif (incluant 'operation': 'transform' ou 'crop').
    """
    if _is_Rt_spec(spec):
        return apply_transform_to_image_file(src_path, dst_path, spec)

    op = _which_op(spec)

    if op == "transform":
        # Appelle ta fonction existante (16→8 bits mono). Si l'entrée est 8 bits, la sortie restera 8 bits.
        res = transform_tiff16_to_tiff8(
            src_path=src_path,
            dst_path=dst_path,
            transform_spec=spec,
            default_he_bins=default_he_bins,
            default_clahe_clip=default_clahe_clip,
        )
        res["operation"] = "transform"
        return res

    elif op == "crop":
        # Appelle la fonction de crop fournie (préserve profondeur/canaux)
        res = crop_tiff_by_spec(
            src_path=src_path,
            dst_path=dst_path,
            crop_spec=spec,
        )
        res["operation"] = "crop"
        return res

    else:
        # Ne devrait pas arriver grâce à _which_op
        raise ValueError(f"Unsupported operation: {op}")



def transform_tiff16_to_tiff8(src_path: str, dst_path: str, transform_spec: str,
                              default_he_bins: int = 256, default_clahe_clip: float = 0.01):
    """
    Applique une transformation 16->8 bits conforme au viewer, sans interface.
    - src_path : chemin TIFF 16 bits mono (ou multi, on prend le 1er canal)
    - dst_path : chemin TIFF 8 bits mono à écrire
    - transform_spec : chaîne "Transform | Min (I16)=... | Max (I16)=... | Mode = ..."
                       éventuellement avec "HE bins = N" ou "CLAHE clip = x.xxx"

    Retourne un dict récapitulatif (bornes utilisées, mode, etc.).
    """
    # ---- parse la spec
    cfg = _parse_transform_spec(transform_spec)
    lv, hv = cfg["low_val"], cfg["high_val"]
    mode = cfg["mode"]
    he_bins = cfg["he_bins"] if cfg["he_bins"] is not None else int(default_he_bins)
    clahe_clip = cfg["clahe_clip"] if cfg["clahe_clip"] is not None else float(default_clahe_clip)

    # ---- charge l'image 16 bits
    arr = tiff.imread(src_path)
    if arr.ndim == 3:
        # si multi-canaux, on prend le 1er
        arr = arr[..., 0]
    if arr.dtype != np.uint16:
        arr = arr.astype(np.uint16, copy=False)
    arr16 = np.ascontiguousarray(arr)
    h, w = arr16.shape

    # ---- normalisation par bornes (exactement comme dans le viewer)
    rng = float(max(1, hv - lv))
    t = (arr16.astype(np.int32) - lv) / rng
    t = np.clip(t, 0.0, 1.0).astype(np.float32)

    # ---- applique la courbe / HE / CLAHE en réutilisant les helpers du module
    if mode == "he":
        y = he_on_unit_float(t, nbins=int(he_bins))
    elif mode == "clahe":
        y = clahe_on_unit_float(t, clip_limit=float(clahe_clip), nbins=int(he_bins))
    elif mode == "wallis":
        # valeurs par défaut si non précisées
        mu_t = cfg.get("wallis_mu") if cfg.get("wallis_mu") is not None else 127.0
        sigma_t = cfg.get("wallis_sigma") if cfg.get("wallis_sigma") is not None else 35.0
        win_sz = cfg.get("wallis_win") if cfg.get("wallis_win") is not None else 15
        # application du filtre (t est déjà normalisé [0,1])
        y = wallis_filter(t, win_size=int(win_sz),
                          mu_target=float(mu_t), sigma_target=float(sigma_t))
    else:
        # réutilise la même logique que le viewer
        y = Tiff16Viewer.apply_curve_pointwise(t, mode)

    out = np.clip(y * 255.0, 0.0, 255.0).astype(np.uint8)

    # ---- écrit le TIFF 8 bits mono
    # Photometric minisblack pour un grayscale standard
    tiff.imwrite(dst_path, out, dtype=np.uint8, photometric='minisblack')

    return {
        "src": src_path,
        "dst": dst_path,
        "height": int(h),
        "width": int(w),
        "low_val": int(lv),
        "high_val": int(hv),
        "mode": mode,
        "he_bins": int(he_bins) if mode in ("he", "clahe") else None,
        "clahe_clip": float(clahe_clip) if mode == "clahe" else None,
        "wallis_mu": int(mu_t) if mode == "wallis" else None,
        "wallis_sigma": int(sigma_t) if mode == "wallis" else None,
        "wallis_win": int(win_sz) if mode == "wallis" else None,
    }















def batch_process_tiff_folder(
    input_dir: str,
    output_dir: str,
    spec: str,
    default_he_bins: int = 256,
    default_clahe_clip: float = 0.01,
) -> Dict[str, Any]:
    """
    Applique `process_tiff_spec` à tous les fichiers .tif/.tiff du dossier d'entrée
    et écrit les résultats dans le dossier de sortie (même nom de fichier).

    Paramètres
    ----------
    input_dir : str
        Dossier contenant les images .tif/.tiff à traiter (non récursif).
    output_dir : str
        Dossier où écrire les résultats (créé si nécessaire).
    spec : str
        Chaîne d'opération ("Transform | ..." OU "Crop | ...").
    default_he_bins : int
        Paramètre par défaut pour HE/CLAHE si non précisé dans la spec Transform.
    default_clahe_clip : float
        Paramètre par défaut pour CLAHE si non précisé dans la spec Transform.

    Retour
    ------
    dict : résumé d’exécution, incluant la liste détaillée des fichiers traités.
    """
    if not os.path.isdir(input_dir):
        raise ValueError(f"Input directory does not exist or is not a directory: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Liste des TIF/TIFF (non récursif)
    exts = {".tif", ".tiff"}
    names = sorted(
        [n for n in os.listdir(input_dir) if os.path.splitext(n)[1].lower() in exts],
        key=lambda s: s.lower()
    )

    results: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    for idx,name in enumerate(names):
        src = os.path.join(input_dir, name)
        dst = os.path.join(output_dir, name)
        print("process",idx+1,"/",len(names))
        try:
            info = process_tiff_spec(
                src_path=src,
                dst_path=dst,
                spec=spec,
                default_he_bins=default_he_bins,
                default_clahe_clip=default_clahe_clip,
            )
            info.update({"src": src, "dst": dst, "ok": True})
            results.append(info)
            processed += 1
        except Exception as e:
            print(str(e))
            results.append({"src": src, "dst": dst, "ok": False, "error": str(e)})
            failed += 1

    return {
        "input_dir": os.path.abspath(input_dir),
        "output_dir": os.path.abspath(output_dir),
        "spec": spec,
        "total": len(names),
        "processed": processed,
        "failed": failed,
        "results": results,
    }



def batch_process_tiff_files(
    input_files: List[str],
    output_files: List[str],
    spec: List[str],
    progress_callback=None,
    argself=None
) -> Dict[str, Any]:
    """
    Applique `process_tiff_spec` à chaque paire (input_files[i], output_files[i]).
    Les deux listes doivent être de même longueur.

    Paramètres
    ----------
    input_files : List[str]
        Liste des chemins de fichiers TIFF source.
    output_files : List[str]
        Liste des chemins de fichiers TIFF destination (même longueur que input_files).
    spec : str
        Chaîne d'opération ("Transform | ..." OU "Crop | ...").
    default_he_bins : int
        Paramètre par défaut pour HE/CLAHE si non précisé dans la spec Transform.
    default_clahe_clip : float
        Paramètre par défaut pour CLAHE si non précisé dans la spec Transform.

    Retour
    ------
    dict : résumé d’exécution, incluant les résultats fichier par fichier.
    """
    default_he_bins = 256
    default_clahe_clip = 0.01
    if len(input_files) != len(output_files):
        raise ValueError(f"input_files and output_files must have the same length "
                         f"({len(input_files)} vs {len(output_files)}).")

    results: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    total = len(input_files)
    for idx, (src, dst) in enumerate(zip(input_files, output_files), start=0):
        print(f"process {idx+1}/{total}")
        if progress_callback is not None:
            progress_value = float(100 * (idx + 1) /total)
            progress_callback(progress_value)
        if argself is not None:
            if argself.stop:
                break
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
            print(f"removed existing file: {dst}")
        try:
            info = process_tiff_spec(
                src_path=src,
                dst_path=dst,
                spec=spec[idx],
                default_he_bins=default_he_bins,
                default_clahe_clip=default_clahe_clip,
            )
            if isinstance(info,str):
                results.append({"src": src, "dst": dst, "ok": True})
            else:
                info.update({"src": src, "dst": dst, "ok": True})
                results.append(info)
            processed += 1
        except Exception as e:
            print("error batch_process_tiff_files ",e)
            results.append({"src": src, "dst": dst, "ok": False, "error": str(e)})
            failed += 1

    return {
        "spec": spec,
        "total": total,
        "processed": processed,
        "failed": failed,
        "results": results,
    }



# read batch_process_tiff_folder !!!
# usage hors orange
# from tiff16_viewer import transform_tiff16_to_tiff8
#
# spec = "Transform | Min (I16) = 36727 | Max (I16) = 61597 | Mode = Lineaire"
# info = transform_tiff16_to_tiff8(r"C:\in.tif", r"C:\out.tif", spec)
# print(info)

# 1) Transform (avec Wallis)
# spec = "Transform | Min (I16) = 0 | Max (I16) = 65535 | Mode = Wallis | Wallis average=127 | standard deviation=103 | win_size=9"
# info = process_tiff_spec(r"C:\in16.tif", r"C:\out8.tif", spec)
# print(info["operation"], info["mode"], info["low_val"], info["high_val"])
#
# # 2) Crop
# spec = "Crop | line = 0 | col = 12 | delta_line = 50 | delta_col = 22"
# info = process_tiff_spec(r"C:\in_any.tif", r"C:\out_crop.tif", spec)
# print(info["operation"], info["output_shape"])

# "Transform | Min (I16) = 0 | Max (I16) = 65535 | Mode = Wallis | Wallis average=127 | standard deviation=103 | win_size=9"
# batch_process_tiff_folder('C:/input/','C:/Users/jean-/Desktop/output/',"Transform | Min (I16) = 0 | Max (I16) = 65535 | Mode = Wallis | Wallis average=127 | standard deviation=103 | win_size=9")
