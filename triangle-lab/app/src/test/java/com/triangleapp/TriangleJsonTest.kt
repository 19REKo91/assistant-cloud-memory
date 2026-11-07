package com.triangleapp

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Test

class TriangleJsonTest {
    @Test fun importsStructuredGeometryExportV2() {
        val json = JSONObject(
            """{
              "schema":"triangle-lab.geometry-export.v2",
              "application":"Triangle Lab",
              "coordinate_system":"2D Euclidean Cartesian",
              "side_convention":"a=BC, b=CA, c=AB",
              "current_triangle":{
                "vertices":{
                  "A":{"x":0.0,"y":0.0},
                  "B":{"x":3.0,"y":0.0},
                  "C":{"x":0.0,"y":4.0}
                },
                "sides":{"a_BC":5.0,"b_CA":4.0,"c_AB":3.0},
                "area":6.0,
                "perimeter":12.0
              }
            }"""
        )

        val triangle = triangleFromJson(json)
        assertEquals(5.0, triangle.a, 1e-9)
        assertEquals(4.0, triangle.b, 1e-9)
        assertEquals(3.0, triangle.c, 1e-9)
        assertEquals(6.0, triangle.area, 1e-9)
    }

    @Test fun keepsImportingLegacyFlatClipboardJson() {
        val json = JSONObject(
            """{"ax":0.0,"ay":0.0,"bx":3.0,"by":0.0,"cx":0.0,"cy":4.0}"""
        )

        val triangle = triangleFromJson(json)
        assertEquals(5.0, triangle.a, 1e-9)
        assertEquals(4.0, triangle.b, 1e-9)
        assertEquals(3.0, triangle.c, 1e-9)
    }
}
