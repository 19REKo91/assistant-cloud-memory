package com.triangleapp

import com.triangleapp.geometry.Triangle
import com.triangleapp.geometry.Vec2
import org.json.JSONObject

/** Keep the compact legacy clipboard format for backward-compatible exports. */
internal fun triangleToJson(t: Triangle): JSONObject = JSONObject().apply {
    put("ax", t.A.x); put("ay", t.A.y)
    put("bx", t.B.x); put("by", t.B.y)
    put("cx", t.C.x); put("cy", t.C.y)
}

/**
 * Imports the legacy flat format and the structured triangle-lab.geometry-export.v2 format.
 * The v2 coordinates are read from current_triangle.vertices.A/B/C.
 */
internal fun triangleFromJson(json: JSONObject): Triangle {
    val source = json.optJSONObject("current_triangle")
        ?: json.optJSONObject("triangle")
        ?: json

    val vertices = source.optJSONObject("vertices") ?: json.optJSONObject("vertices")
    if (vertices != null) {
        fun point(name: String): Vec2 {
            val item = vertices.getJSONObject(name)
            return Vec2(item.getDouble("x"), item.getDouble("y"))
        }
        return Triangle(point("A"), point("B"), point("C"))
    }

    // Older clipboard exports use ax/ay, bx/by and cx/cy at the root.
    val flat = if (source.has("ax")) source else json
    val required = listOf("ax", "ay", "bx", "by", "cx", "cy")
    require(required.all { flat.has(it) }) {
        "JSON does not contain supported Triangle Lab vertex coordinates"
    }
    return Triangle(
        Vec2(flat.getDouble("ax"), flat.getDouble("ay")),
        Vec2(flat.getDouble("bx"), flat.getDouble("by")),
        Vec2(flat.getDouble("cx"), flat.getDouble("cy"))
    )
}
