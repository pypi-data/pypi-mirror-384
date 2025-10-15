from __future__ import annotations

import io
import webbrowser
from pathlib import Path
from typing import Callable

import numpy as np
from matplotlib import pyplot as plt
from plotly import graph_objects as go
from pydantic import Field

from .core import pdf
from .core.plotly_utils import add_title
from .core.profile import CollapsedCircleProfile
from .core.roi import DiskROI
from .core.scale import wrap360
from .core.utilities import QuaacDatum, ResultBase, ResultsDataMixin
from .core.warnings import capture_warnings
from .ct import CatPhanBase, CatPhanModule, Slice


class TomoCheeseResult(ResultBase):
    """This class should not be called directly. It is returned by the ``results_data()`` method.
    It is a dataclass under the hood and thus comes with all the dunder magic.

    Use the following attributes as normal class attributes."""

    origin_slice: int = Field(
        description="The slice index that was used for the ROI analysis.",
        title="Slice number of the analyzed image",
    )
    num_images: int = Field(
        description="The number of images that were in the passed dataset.",
        title="Number of images in the stack",
    )
    phantom_roll: float = Field(
        description="The roll of the phantom in degrees.",
        title="Phantom roll (\N{DEGREE SIGN})",
    )
    rois: dict[str, dict[str, int | float]] = Field(
        description="A dictionary of measured ROIs.", title="ROI data"
    )
    # having explicit rois here is a stupid idea. Keeping it for backwards compatibility.
    # `rois` is the new way to go as its extensible for N ROIs.
    roi_1: dict = Field(title="ROI 1")
    roi_2: dict = Field(title="ROI 2")
    roi_3: dict = Field(title="ROI 3")
    roi_4: dict = Field(title="ROI 4")
    roi_5: dict = Field(title="ROI 5")
    roi_6: dict = Field(title="ROI 6")
    roi_7: dict = Field(title="ROI 7")
    roi_8: dict = Field(title="ROI 8")
    roi_9: dict = Field(title="ROI 9")
    roi_10: dict = Field(title="ROI 10")
    roi_11: dict = Field(title="ROI 11")
    roi_12: dict = Field(title="ROI 12")
    roi_13: dict = Field(title="ROI 13")
    roi_14: dict = Field(title="ROI 14")
    roi_15: dict = Field(title="ROI 15")
    roi_16: dict = Field(title="ROI 16")
    roi_17: dict = Field(title="ROI 17")
    roi_18: dict = Field(title="ROI 18")
    roi_19: dict = Field(title="ROI 19")
    roi_20: dict = Field(title="ROI 20")


class CheeseResult(ResultBase):
    """This class should not be called directly. It is returned by the ``results_data()`` method.
    It is a dataclass under the hood and thus comes with all the dunder magic.

    Use the following attributes as normal class attributes."""

    origin_slice: int = Field(
        description="The slice index that was used for the ROI analysis.",
        title="Slice number of the analyzed image",
    )
    num_images: int = Field(
        description="The number of images that were in the passed dataset.",
        title="Number of images in the stack",
    )
    phantom_roll: float = Field(
        description="The roll of the phantom in degrees.",
        title="Phantom roll (\N{DEGREE SIGN})",
    )
    rois: dict[str, dict[str, int | float]] = Field(
        description="A dictionary of measured ROIs.", title="ROI data"
    )


class CheeseModule(CatPhanModule):
    """A base class for cheese-like phantom modules. Each phantom should have only one module. Inherit from this class
    and populate all attributes"""

    common_name: str
    rois: dict[str, DiskROI]
    roi_settings: dict[str, dict[str, float]]

    def _setup_rois(self) -> None:
        # unlike its super, we use simple disk ROIs as we're not doing complicated things.
        for name, setting in self.roi_settings.items():
            self.rois[name] = DiskROI.from_phantom_center(
                self.image,
                setting["angle_corrected"],
                setting["radius_pixels"],
                setting["distance_pixels"],
                self.phan_center,
            )

    def plot_rois(self, axis: plt.Axes) -> None:
        """Plot the ROIs to the axis. We add the ROI # to help the user differentiate"""
        for name, roi in self.rois.items():
            roi.plot2axes(axis, edgecolor="blue", text=name)

    def plotly_rois(self, fig: go.Figure) -> None:
        """Plot the ROIs to the figure. We add the ROI # to help the user differentiate"""
        for name, roi in self.rois.items():
            roi.plotly(
                fig,
                name=name,
                line_color="blue",
            )


class TomoCheeseModule(CheeseModule):
    """The pluggable module with user-accessible holes.

    The ROIs of the inner circle are ~45 degrees apart. The ROIs of the outer circle are ~30 degrees apart.

    """

    common_name = "Tomo Cheese"
    inner_roi_dist_mm = 65
    outer_roi_dist_mm = 110
    roi_radius_mm = 12
    roi_settings = {
        "1": {
            "angle": -75,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "2": {
            "angle": -67.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "3": {
            "angle": -45,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "4": {
            "angle": -22.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "5": {
            "angle": -15,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "6": {
            "angle": 15,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "7": {
            "angle": 22.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "8": {
            "angle": 45,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "9": {
            "angle": 67.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "10": {
            "angle": 75,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "11": {
            "angle": 105,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "12": {
            "angle": 112.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "13": {
            "angle": 135,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "14": {
            "angle": 157.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "15": {
            "angle": 165,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "16": {
            "angle": -165,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "17": {
            "angle": -157.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "18": {
            "angle": -135,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "19": {
            "angle": -112.5,
            "distance": inner_roi_dist_mm,
            "radius": roi_radius_mm,
        },
        "20": {
            "angle": -105,
            "distance": outer_roi_dist_mm,
            "radius": roi_radius_mm,
        },
    }


class CheesePhantomBase(CatPhanBase, ResultsDataMixin[CheeseResult]):
    """A base class for doing cheese-like phantom analysis. A subset of catphan analysis where only one module is assumed."""

    model: str
    _demo_url: str
    air_bubble_radius_mm: int | float
    localization_radius: int | float
    min_num_images: int
    catphan_radius_mm: float
    roi_config: dict
    module_class: type[CheeseModule]
    module: CheeseModule
    clip_in_localization = True

    def analyze(
        self,
        roi_config: dict | None = None,
        x_adjustment: float = 0,
        y_adjustment: float = 0,
        angle_adjustment: float = 0,
        roi_size_factor: float = 1,
        scaling_factor: float = 1,
        origin_slice: int | None = None,
    ) -> None:
        """Analyze the Tomo Cheese phantom.

        Parameters
        ----------
        roi_config : dict
            The configuration of the ROIs, specifically the known densities.
        x_adjustment: float
            A fine-tuning adjustment to the detected x-coordinate of the phantom center. This will move the
            detected phantom position by this amount in the x-direction in mm. Positive values move the phantom to the right.
        y_adjustment: float
            A fine-tuning adjustment to the detected y-coordinate of the phantom center. This will move the
            detected phantom position by this amount in the y-direction in mm. Positive values move the phantom down.
        angle_adjustment: float
            A fine-tuning adjustment to the detected angle of the phantom. This will rotate the phantom by this amount in degrees.
            Positive values rotate the phantom clockwise.
        roi_size_factor: float
            A fine-tuning adjustment to the ROI sizes of the phantom. This will scale the ROIs by this amount.
            Positive values increase the ROI sizes. In contrast to the scaling adjustment, this
            adjustment effectively makes the ROIs bigger or smaller, but does not adjust their position.
        scaling_factor: float
            A fine-tuning adjustment to the detected magnification of the phantom. This will zoom the ROIs and phantom outline (if applicable) by this amount.
            In contrast to the roi size adjustment, the scaling adjustment effectively moves the phantom and ROIs
            closer or further from the phantom center. I.e. this zooms the outline and ROI positions, but not ROI size.
        origin_slice : int, None
            The slice number to analyze. If None, the slice will be automatically determined. This is a fallback
            method in case the automatic slice detection fails.
        """
        self.x_adjustment = x_adjustment
        self.y_adjustment = y_adjustment
        self.angle_adjustment = angle_adjustment
        self.roi_size_factor = roi_size_factor
        self.scaling_factor = scaling_factor
        self.localize(origin_slice=origin_slice)
        self.module = self.module_class(self, clear_borders=self.clear_borders)
        self.roi_config = roi_config

    def _roi_angles(self) -> list[float]:
        return [wrap360(s["angle"]) for s in self.module_class.roi_settings.values()]

    def _ensure_physical_scan_extent(self) -> bool:
        """The cheese phantom only has one module."""
        return True

    def find_phantom_roll(self, func: Callable | None = None) -> float:
        """Examine the phantom for the maximum HU delta insert position. Roll the phantom by the
        measured angle to the nearest nominal angle if nearby. If not nearby, default to 0
        """
        # get edges and make ROIs from it
        slice = Slice(self, self.origin_slice, clear_borders=self.clear_borders)
        circle = CollapsedCircleProfile(
            slice.phan_center,
            self.localization_radius / self.mm_per_pixel,
            slice.image.array,
            ccw=False,
            width_ratio=0.05,
            num_profiles=5,
        )
        # we only want peaks. air pockets can cause bad range shifts so set min to 0
        circle.values = np.where(circle.values < 0, 0, circle.values)
        peak_idxs, _ = circle.find_fwxm_peaks(max_number=1)
        if peak_idxs:
            angle = peak_idxs[0] / len(circle) * 360
            # see if angle is near an ROI node
            shifts = [angle - a for a in self._roi_angles()]
            min_shift = shifts[np.argmin([abs(shift) for shift in shifts])]
            if -5 < min_shift < 5:
                return min_shift
            else:
                print(
                    f"Detected shift of {min_shift} was >5 degrees; automatic roll compensation aborted. Setting roll to 0."
                )
                return 0
        else:
            print(
                "No low-HU regions found in the outer ROI circle; automatic roll compensation aborted. Setting roll to 0."
            )
            return 0

    def plotly_analyzed_images(
        self,
        show: bool = True,
        show_colorbar: bool = True,
        show_legend: bool = True,
        **kwargs,
    ) -> dict[str, go.Figure]:
        """Plot the analyzed set of images to Plotly figures.


        Parameters
        ----------
        show : bool
            Whether to show the plot.
        show_colorbar : bool
            Whether to show the colorbar on the plot.
        show_legend : bool
            Whether to show the legend on the plot.
        kwargs
            Additional keyword arguments to pass to the plot.

        Returns
        -------
        dict
            A dictionary of the Plotly figures where the key is the name of the
            image and the value is the figure.
        """
        figs = {
            self.module.common_name: self.module.plotly(
                show_colorbar=show_colorbar, show_legend=show_legend, **kwargs
            )
        }

        # density curve (if densities passed)
        if self.roi_config:
            xs = []
            ys = []
            for roi_num, roi_data in self.roi_config.items():
                xs.append(roi_data["density"])
                ys.append(self.module.rois[roi_num].pixel_value)
            # sort by HU so it looks like a normal curve; ROI densities can be out of order
            sorted_args = np.argsort(xs)
            xs = np.array(xs)[sorted_args]
            ys = np.array(ys)[sorted_args]
            # plot
            density_fig = go.Figure()
            density_fig.add_scatter(
                x=xs,
                y=ys,
                mode="lines+markers",
                line_dash="dash",
                marker_symbol="diamond",
            )
            density_fig.update_layout(
                yaxis_title="HU",
                xaxis_title="Density",
            )
            add_title(density_fig, "Density vs HU curve")
            figs["Density vs HU curve"] = density_fig

        if show:
            for fig in figs.values():
                fig.show()
        return figs

    def plot_analyzed_image(self, show: bool = True, **plt_kwargs: dict) -> None:
        """Plot the images used in the calculation and summary data.

        Parameters
        ----------
        show : bool
            Whether to plot the image or not.
        plt_kwargs : dict
            Keyword args passed to the plt.figure() method. Allows one to set things like figure size.
        """
        fig, ax = plt.subplots(**plt_kwargs)
        self.module.plot(ax)
        plt.tight_layout()
        if show:
            plt.show()

    def results(self, as_list: bool = False) -> str | list[str]:
        """Return the results of the analysis as a string. Use with print().

        Parameters
        ----------
        as_list : bool
            Whether to return as a list of strings vs single string. Pretty much for internal usage.
        """
        results = [
            f" - {self.model} Phantom Analysis - ",
            " - HU Module - ",
        ]
        results += [
            f"ROI {name} median: {roi.pixel_value:.1f}, stdev: {roi.std:.1f}"
            for name, roi in self.module.rois.items()
        ]
        if as_list:
            return results
        else:
            return "\n".join(results)

    def plot_density_curve(self, show: bool = True, **plt_kwargs: dict):
        """Plot the densities of the ROIs vs the measured HU. This will sort the ROIs by measured HU before plotting.

        Parameters
        ----------
        show : bool
            Whether to plot the image or not.
        plt_kwargs : dict
            Keyword args passed to the plt.figure() method. Allows one to set things like figure size.
        """
        if not self.roi_config:
            raise ValueError(
                "No ROI density configuration was passed to the analyze method. Re-analyze with densities first."
            )
        xs = []
        ys = []
        for roi_num, roi_data in self.roi_config.items():
            xs.append(roi_data["density"])
            ys.append(self.module.rois[roi_num].pixel_value)
        # sort by HU so it looks like a normal curve; ROI densities can be out of order
        sorted_args = np.argsort(xs)
        xs = np.array(xs)[sorted_args]
        ys = np.array(ys)[sorted_args]
        # plot
        fig, ax = plt.subplots(**plt_kwargs)
        ax.plot(xs, ys, linestyle="-.", marker="D")
        ax.set_title("Density vs HU curve")
        ax.set_ylabel("HU")
        ax.set_xlabel("Density")
        ax.grid("on")
        plt.tight_layout()
        if show:
            plt.show()

    def _quaac_datapoints(self) -> dict[str, QuaacDatum]:
        results_data = self.results_data(as_dict=True)
        data = {}
        data["Phantom roll"] = QuaacDatum(
            value=results_data["phantom_roll"],
            unit="degrees",
        )
        for roi_num, roi_data in results_data["rois"].items():
            data[f"ROI {roi_num}"] = QuaacDatum(
                value=roi_data["median"],
                unit="HU",
            )
        return data

    def publish_pdf(
        self,
        filename: str | Path,
        notes: str | None = None,
        open_file: bool = False,
        metadata: dict | None = None,
        logo: Path | str | None = None,
    ) -> None:
        """Publish (print) a PDF containing the analysis and quantitative results.

        Parameters
        ----------
        filename : (str, file-like object}
            The file to write the results to.
        notes : str, list of strings
            Text; if str, prints single line.
            If list of strings, each list item is printed on its own line.
        open_file : bool
            Whether to open the file using the default program after creation.
        metadata : dict
            Extra data to be passed and shown in the PDF. The key and value will be shown with a colon.
            E.g. passing {'Author': 'James', 'Unit': 'TrueBeam'} would result in text in the PDF like:
            --------------
            Author: James
            Unit: TrueBeam
            --------------
        logo: Path, str
            A custom logo to use in the PDF report. If nothing is passed, the default pylinac logo is used.
        """
        canvas = pdf.PylinacCanvas(
            filename,
            page_title=f"{self.model} Phantom",
            metadata=metadata,
            logo=logo,
        )
        if notes is not None:
            canvas.add_text(text="Notes:", location=(1, 4.5), font_size=14)
            canvas.add_text(text=notes, location=(1, 4))

        canvas.add_text(text=self.results(as_list=True), location=(3, 23), font_size=16)
        data = io.BytesIO()
        self.save_analyzed_image(data)
        canvas.add_new_page()
        canvas.add_image(data, location=(0, 4), dimensions=(22, 22))
        canvas.finish()
        if open_file:
            webbrowser.open(filename)

    def save_analyzed_subimage(self) -> None:
        raise NotImplementedError("There are no sub-images for cheese-like phantoms")

    def plot_analyzed_subimage(self) -> None:
        raise NotImplementedError("There are no sub-images for cheese-like phantoms")

    def _generate_results_data(self) -> CheeseResult:
        return CheeseResult(
            origin_slice=self.origin_slice,
            num_images=self.num_images,
            phantom_roll=self.catphan_roll,
            rois={name: roi.as_dict() for name, roi in self.module.rois.items()},
        )


@capture_warnings
class TomoCheese(CheesePhantomBase, ResultsDataMixin[TomoCheeseResult]):
    """A class for analyzing the TomoTherapy 'Cheese' Phantom containing insert holes and plugs for HU analysis."""

    model = "Tomotherapy Cheese"
    _demo_url = "TomoCheese.zip"
    air_bubble_radius_mm = 14
    localization_radius = 110
    min_num_images = 10
    catphan_radius_mm = 150
    module_class = TomoCheeseModule
    module: TomoCheeseModule

    @staticmethod
    def run_demo(show: bool = True):
        """Run the Tomotherapy Cheese demo"""
        cheese = TomoCheese.from_demo_images()
        cheese.analyze()
        print(cheese.results())
        cheese.plot_analyzed_image(show)

    def _generate_results_data(self):
        """Return the results of the analysis as a structure dataclass"""
        return TomoCheeseResult(
            origin_slice=self.origin_slice,
            num_images=self.num_images,
            phantom_roll=self.catphan_roll,
            rois={name: roi.as_dict() for name, roi in self.module.rois.items()},
            roi_1=self.module.rois["1"].as_dict(),
            roi_2=self.module.rois["2"].as_dict(),
            roi_3=self.module.rois["3"].as_dict(),
            roi_4=self.module.rois["4"].as_dict(),
            roi_5=self.module.rois["5"].as_dict(),
            roi_6=self.module.rois["6"].as_dict(),
            roi_7=self.module.rois["7"].as_dict(),
            roi_8=self.module.rois["8"].as_dict(),
            roi_9=self.module.rois["9"].as_dict(),
            roi_10=self.module.rois["10"].as_dict(),
            roi_11=self.module.rois["11"].as_dict(),
            roi_12=self.module.rois["12"].as_dict(),
            roi_13=self.module.rois["13"].as_dict(),
            roi_14=self.module.rois["14"].as_dict(),
            roi_15=self.module.rois["15"].as_dict(),
            roi_16=self.module.rois["16"].as_dict(),
            roi_17=self.module.rois["17"].as_dict(),
            roi_18=self.module.rois["18"].as_dict(),
            roi_19=self.module.rois["19"].as_dict(),
            roi_20=self.module.rois["20"].as_dict(),
        )


class CIRSHUModule(CheeseModule):
    """The pluggable module with user-accessible holes.

    The ROIs of each circle are ~45 degrees apart.
    """

    common_name = "CIRS electron density"
    outer_radius_mm = 115
    inner_radius_mm = 60
    roi_radius_mm = 10
    roi_settings = {
        "1": {
            "angle": 0,
            "distance": 0,
            "radius": roi_radius_mm,
        },
        "2": {
            "angle": -90,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "3": {
            "angle": -90,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
        "4": {
            "angle": -45,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "5": {
            "angle": -45,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
        "6": {
            "angle": 0,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "7": {
            "angle": 0,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
        "8": {
            "angle": 45,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "9": {
            "angle": 45,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
        "10": {
            "angle": 90,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        # this one is closer to the ring; presumably because the bottom of the phantom is flatter than the top
        "11": {
            "angle": 90,
            "distance": outer_radius_mm - 5,
            "radius": roi_radius_mm,
        },
        "12": {
            "angle": 135,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "13": {
            "angle": 135,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
        "14": {
            "angle": 180,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "15": {
            "angle": 180,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
        "16": {
            "angle": -135,
            "distance": inner_radius_mm,
            "radius": roi_radius_mm,
        },
        "17": {
            "angle": -135,
            "distance": outer_radius_mm,
            "radius": roi_radius_mm,
        },
    }


@capture_warnings
class CIRS062M(CheesePhantomBase):
    """A class for analyzing the CIRS Electron Density Phantom containing insert holes and plugs for HU analysis.

    See Also
    --------
    https://www.cirsinc.com/products/all/24/electron-density-phantom/
    """

    model = "CIRS Electron Density (062M)"
    air_bubble_radius_mm = 30
    clear_borders = False
    hu_origin_slice_variance = 150
    localization_radius = 115
    catphan_radius_mm = 155
    min_num_images = 10
    roi_config: dict
    module_class = CIRSHUModule
    module: CIRSHUModule

    @classmethod
    def from_demo_images(cls):
        raise NotImplementedError("No demo images available for this phantom")

    def find_origin_slice(self) -> int:
        """We override to lower the minimum variation required. This is ripe for refactor, but I'd like to
        add a few more phantoms first to get the full picture required."""
        hu_slices = []
        for image_number in range(0, self.num_images, 2):
            slice = Slice(
                self, image_number, combine=False, clear_borders=self.clear_borders
            )
            if slice.is_phantom_in_view():
                circle_prof = CollapsedCircleProfile(
                    slice.phan_center,
                    radius=self.localization_radius / self.mm_per_pixel,
                    image_array=slice.image,
                    width_ratio=0.05,
                    num_profiles=5,
                )
                prof = circle_prof.values
                # determine if the profile contains both low and high values and that most values are the same
                low_end, high_end = np.percentile(prof, [2, 98])
                median = np.median(prof)
                ##################################
                # the difference from the original
                ##################################
                middle_variation = np.percentile(prof, 60) - np.percentile(prof, 40)
                variation_limit = max(
                    100, self.dicom_stack.metadata.SliceThickness * -100 + 300
                )
                if (
                    (low_end < median - self.hu_origin_slice_variance)
                    or (high_end > median + self.hu_origin_slice_variance)
                    and (middle_variation < variation_limit)
                ):
                    hu_slices.append(image_number)

        if not hu_slices:
            raise ValueError(
                "No slices were found that resembled the HU linearity module"
            )
        hu_slices = np.array(hu_slices)
        c = int(round(float(np.median(hu_slices))))
        ln = len(hu_slices)
        # drop slices that are way far from median
        hu_slices = hu_slices[((c + ln / 2) >= hu_slices) & (hu_slices >= (c - ln / 2))]
        center_hu_slice = int(round(float(np.median(hu_slices))))
        if self._is_within_image_extent(center_hu_slice):
            return center_hu_slice
