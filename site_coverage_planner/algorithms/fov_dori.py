"""Processing algorithm: camera FoV footprint + DORI band polygons.

Reads a point layer of camera positions carrying the optics attributes as
fields, and emits one FoV footprint polygon (out to the detect range) plus
four DORI band polygons (identify/recognise/observe/detect) per input
point. Pure geometry from :mod:`site_coverage_planner.optics` — no
terrain/viewshed intersect yet (tracked as a follow-up).
"""

from __future__ import annotations

from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from ..optics import Camera

REQUIRED_FIELDS = (
    "focal_length_mm",
    "sensor_width_mm",
    "sensor_height_mm",
    "h_resolution_px",
    "v_resolution_px",
    "heading_deg",
)


class CameraFovDoriAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT_FOV = "OUTPUT_FOV"
    OUTPUT_DORI = "OUTPUT_DORI"

    def tr(self, text: str) -> str:
        return QCoreApplication.translate("CameraFovDoriAlgorithm", text)

    def createInstance(self):
        return CameraFovDoriAlgorithm()

    def name(self) -> str:
        return "camera_fov_dori"

    def displayName(self) -> str:
        return self.tr("Camera FoV + DORI bands")

    def group(self) -> str:
        return self.tr("Site Coverage Planner")

    def groupId(self) -> str:
        return "site_coverage_planner"

    def shortHelpString(self) -> str:
        return self.tr(
            "Builds a FoV footprint polygon and four DORI band polygons "
            "(identify/recognise/observe/detect) for each camera point. "
            "The point layer must carry fields: " + ", ".join(REQUIRED_FIELDS)
        )

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr("Camera points"),
                [QgsProcessing.TypeVectorPoint],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT_FOV, self.tr("FoV footprint"))
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT_DORI, self.tr("DORI bands"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        missing = [f for f in REQUIRED_FIELDS if source.fields().indexOf(f) < 0]
        if missing:
            raise QgsProcessingException(
                "Camera points layer is missing required field(s): " + ", ".join(missing)
            )

        fov_fields = QgsFields()
        fov_fields.append(QgsField("camera_id", QVariant.LongLong))

        dori_fields = QgsFields()
        dori_fields.append(QgsField("camera_id", QVariant.LongLong))
        dori_fields.append(QgsField("dori_level", QVariant.String))

        fov_sink, fov_dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_FOV,
            context,
            fov_fields,
            QgsWkbTypes.Polygon,
            source.sourceCrs(),
        )
        dori_sink, dori_dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_DORI,
            context,
            dori_fields,
            QgsWkbTypes.Polygon,
            source.sourceCrs(),
        )

        total = source.featureCount() or 1
        for current, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            point = feature.geometry().asPoint()
            camera = Camera(
                focal_length_mm=float(feature["focal_length_mm"]),
                sensor_width_mm=float(feature["sensor_width_mm"]),
                sensor_height_mm=float(feature["sensor_height_mm"]),
                h_resolution_px=int(feature["h_resolution_px"]),
                v_resolution_px=int(feature["v_resolution_px"]),
            )
            heading_deg = float(feature["heading_deg"])
            origin = (point.x(), point.y())

            fov_range_m = camera.dori_range_m("detect")
            fov_polygon = camera.fov_polygon(origin, heading_deg, fov_range_m)

            fov_feature = QgsFeature(fov_fields)
            fov_feature.setGeometry(
                QgsGeometry.fromPolygonXY([[QgsPointXY(x, y) for x, y in fov_polygon]])
            )
            fov_feature.setAttributes([feature.id()])
            fov_sink.addFeature(fov_feature, QgsFeatureSink.FastInsert)

            for level, band in camera.dori_band_polygons(origin, heading_deg).items():
                band_feature = QgsFeature(dori_fields)
                band_feature.setGeometry(
                    QgsGeometry.fromPolygonXY([[QgsPointXY(x, y) for x, y in band]])
                )
                band_feature.setAttributes([feature.id(), level])
                dori_sink.addFeature(band_feature, QgsFeatureSink.FastInsert)

            feedback.setProgress(int(100 * current / total))

        return {self.OUTPUT_FOV: fov_dest_id, self.OUTPUT_DORI: dori_dest_id}
