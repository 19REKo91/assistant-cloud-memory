package com.triangleapp.geometry

import kotlin.math.max
import kotlin.math.sin
import kotlin.math.sqrt

object GeometryEngine {
    fun triangleFromSides(a: Double, b: Double, c: Double): Triangle? {
        if (!Validation.sides(a, b, c).ok) return null

        // Normalize first to avoid overflow/underflow in the cosine-law squares.
        // Convention: a=BC, b=CA, c=AB. Place A=(0,0), B=(c,0).
        val scale = max(a, max(b, c))
        val an = a / scale
        val bn = b / scale
        val cn = c / scale
        val cxn = (bn * bn + cn * cn - an * an) / (2.0 * cn)
        val cySquared = bn * bn - cxn * cxn
        if (!cxn.isFinite() || !cySquared.isFinite() || cySquared < -1e-12) return null
        val cyn = sqrt(max(0.0, cySquared))
        if (cyn <= 1e-12) return null
        val cx = cxn * scale
        val cy = cyn * scale
        if (!cx.isFinite() || !cy.isFinite()) return null
        return Triangle(Vec2(0.0, 0.0), Vec2(c, 0.0), Vec2(cx, cy))
    }

    fun triangleFromAngles(
        angleAVal: Double,
        angleBVal: Double,
        refSide: Char,
        refLen: Double
    ): Triangle? {
        if (!Validation.angles(angleAVal, angleBVal).ok ||
            !refLen.isFinite() || refLen <= 0.0) return null

        val angleCVal = 180.0 - angleAVal - angleBVal
        val aRad = Math.toRadians(angleAVal)
        val bRad = Math.toRadians(angleBVal)
        val cRad = Math.toRadians(angleCVal)
        val sinA = sin(aRad)
        val sinB = sin(bRad)
        val sinC = sin(cRad)
        if (minOf(sinA, sinB, sinC) <= 0.0) return null

        val (a, b, c) = when (refSide.lowercaseChar()) {
            'a' -> Triple(refLen, refLen * sinB / sinA, refLen * sinC / sinA)
            'b' -> Triple(refLen * sinA / sinB, refLen, refLen * sinC / sinB)
            'c' -> Triple(refLen * sinA / sinC, refLen * sinB / sinC, refLen)
            else -> return null
        }
        return triangleFromSides(a, b, c)
    }

    fun rescaleToReference(tri: Triangle, refSide: Char, newLen: Double): Triangle? {
        if (tri.isDegenerate || !newLen.isFinite() || newLen <= 0.0) return null
        val current = when (refSide.lowercaseChar()) {
            'a' -> tri.a
            'b' -> tri.b
            'c' -> tri.c
            else -> return null
        }
        if (current <= 0.0 || !current.isFinite()) return null
        val factor = newLen / current
        if (!factor.isFinite() || factor <= 0.0) return null
        val result = Triangle(tri.A * factor, tri.B * factor, tri.C * factor)
        return result.takeUnless { it.isDegenerate }
    }
}
