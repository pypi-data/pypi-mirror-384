from abc import ABC, abstractmethod
from typing import List, Optional, Dict

import matplotlib.pyplot as plt
from pydantic import BaseModel


class BasePlot(BaseModel, ABC):
    title: str
    x_label: str
    y_label: str

    @abstractmethod
    def _draw(self):
        pass

    def plot(
        self,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
    ):
        self._plot_common(title, x_label, y_label, show=True)

    def save(
        self,
        filepath: str,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
    ):
        self._plot_common(title, x_label, y_label, show=False, filepath=filepath)

    def _plot_common(
        self,
        title: Optional[str],
        x_label: Optional[str],
        y_label: Optional[str],
        show: bool = True,
        filepath: Optional[str] = None,
    ):
        plt.figure()
        self._draw()
        plt.title(title or self.title)
        plt.xlabel(x_label or self.x_label)
        plt.ylabel(y_label or self.y_label)
        if show:
            plt.show()
        elif filepath:
            plt.savefig(filepath)
            plt.close()


class PlotDataXY(BasePlot):
    x: List[float]
    y: List[float]
    recommended_contour_level: Optional[Dict[str, float]] = None
    resolution: Optional[float] = None

    def _draw(self):
        plt.plot(self.x, self.y)
        if self.recommended_contour_level and "recl" in self.recommended_contour_level:
            recl = self.recommended_contour_level["recl"]
            plt.axvline(x=recl, color='red', linestyle='--', label=f'Recommended Contour Level {recl:.2f}')
        if self.resolution is not None:
            plt.axvline(x=1/self.resolution, color='red', linestyle='--', label=f'Resolution {self.resolution:.2f} Å')
        plt.legend(loc="best")
        plt.grid(True)


class PlotDataHistogram(BasePlot):
    values: List[float]
    counts: List[int]

    def _draw(self):
        x = self.values
        y = self.counts

        # If counts is longer by 1, pad values
        if len(y) > len(x):
            x = [x[0] - 0.1] + x  # prepend a dummy bin edge (or use 0.0)
        elif len(y) < len(x):
            y = [0] + y  # pad counts instead

        if len(x) != len(y):
            raise ValueError(f"Length mismatch: {len(x)=}, {len(y)=}")

        plt.bar(x, y, width=0.2)


class PlotFSC(BasePlot):
    type: str
    pdb_id: Optional[str] = None  # Optional field for PDB ID for mmfsc
    fsc: List[float]
    onebit: Optional[List[float]] = None
    halfbit: Optional[List[float]] = None
    cutoff_0_5: Optional[List[float]] = None
    cutoff_0_143: Optional[List[float]] = None
    level: List[float]
    angstrom_resolution: Optional[List[float]] = None
    phaserandomization: Optional[List[float]] = None
    fsc_masked: Optional[List[float]] = None
    fsc_corrected: Optional[List[float]] = None
    intersections: Dict
    feature_zones: Optional[Dict] = None
    resolution: Optional[float] = None

    def _draw(self):
        # Plot the main FSC curve
        plt.plot(self.level, self.fsc, label="FSC", color="blue")

        if self.onebit:
            plt.plot(self.level, self.onebit, label="1-bit", linestyle="--", color="gray")
        if self.halfbit:
            plt.plot(self.level, self.halfbit, label="0.5-bit", linestyle="--", color="gray")
        if self.cutoff_0_5:
            plt.plot(self.level, self.cutoff_0_5, label="0.5 cutoff", linestyle=":", color="red")
        if self.cutoff_0_143:
            plt.plot(self.level, self.cutoff_0_143, label="0.143 cutoff", linestyle=":", color="orange")
        if self.phaserandomization:
            plt.plot(self.level, self.phaserandomization, label="Phase Randomization", linestyle="-.", color="purple")
        if self.fsc_masked:
            plt.plot(self.level, self.fsc_masked, label="FSC Masked", linestyle="--", color="brown")
        if self.fsc_corrected:
            plt.plot(self.level, self.fsc_corrected, label="FSC Corrected", linestyle="--", color="darkgreen")
        if self.resolution is not None:
            plt.axvline(x=1/self.resolution, color='red', linestyle='--', label=f'Resolution {self.resolution:.2f} Å')

        plt.legend(loc="best")
        plt.grid(True)


class PlotVolumeEstimate(BasePlot):
    volume: List[float]
    level: List[float]
    estimated_volume: float
    recommended_contour_level: Optional[Dict[str, float]] = None

    def _draw(self):
        plt.plot(self.level, self.volume, label="Volume", color="blue")
        if self.estimated_volume is not None:
            plt.axhline(y=self.estimated_volume, color='orange', linestyle='--', label=f'Estimated Volume {self.estimated_volume:.2f} nm³')
        if self.recommended_contour_level and "recl" in self.recommended_contour_level:
            recl = self.recommended_contour_level["recl"]
            plt.axvline(x=recl, color='red', linestyle='--', label=f'Recommended Contour Level {recl:.2f}')

        plt.legend(loc="best")
        plt.grid(True)
