package com.triangleapp.geometry

data class ValidationResult(val ok: Boolean, val message: String? = null)

object Validation {
    fun sides(a: Double, b: Double, c: Double): ValidationResult {
        if (!a.isFinite() || !b.isFinite() || !c.isFinite())
            return ValidationResult(false, "values_finite")
        if (a <= 0.0 || b <= 0.0 || c <= 0.0)
            return ValidationResult(false, "sides_positive")
        // Scaled comparison avoids overflow in a+b for very large finite inputs.
        val scale = maxOf(a, b, c)
        val x = a / scale
        val y = b / scale
        val z = c / scale
        if (x + y <= z || x + z <= y || y + z <= x)
            return ValidationResult(false, "triangle_inequality")
        return ValidationResult(true)
    }

    fun angles(angleA: Double, angleB: Double): ValidationResult {
        if (!angleA.isFinite() || !angleB.isFinite())
            return ValidationResult(false, "values_finite")
        if (angleA <= 0.0 || angleB <= 0.0)
            return ValidationResult(false, "angles_positive")
        if (angleA >= 180.0 || angleB >= 180.0 || angleA + angleB >= 180.0)
            return ValidationResult(false, "angles_sum")
        return ValidationResult(true)
    }
}
