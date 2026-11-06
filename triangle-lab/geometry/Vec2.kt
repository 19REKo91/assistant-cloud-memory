package com.triangleapp.geometry

import kotlin.math.hypot

data class Vec2(val x: Double, val y: Double) {
    operator fun plus(other: Vec2) = Vec2(x + other.x, y + other.y)
    operator fun minus(other: Vec2) = Vec2(x - other.x, y - other.y)
    operator fun times(k: Double) = Vec2(x * k, y * k)
    operator fun div(k: Double) = Vec2(x / k, y / k)

    val length: Double get() = hypot(x, y)
    fun norm(): Vec2 {
        val n = length
        return if (n > 0.0 && n.isFinite()) this / n else Vec2(0.0, 0.0)
    }

    fun isFinite(): Boolean = x.isFinite() && y.isFinite()
}

fun dist(p1: Vec2, p2: Vec2): Double = (p1 - p2).length
