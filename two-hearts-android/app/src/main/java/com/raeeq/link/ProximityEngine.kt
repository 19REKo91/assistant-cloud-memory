package com.raeeq.link

import java.util.ArrayDeque

enum class ProximityState { WAITING, NEAR, APART }

class ProximityEngine(
    private val closeThresholdDbm: Int = -56,
    private val departureDelayMs: Long = 10_000L,
    private val stableWindowMs: Long = 2_500L,
    private val requiredStrongSamples: Int = 3
) {
    private data class Reading(val timeMs: Long, val rssi: Int)
    private val readings = ArrayDeque<Reading>()
    var state: ProximityState = ProximityState.WAITING
        private set
    var latestRssi: Int? = null
        private set
    private var lastStrongAt: Long? = null

    fun onRssi(rssi: Int, nowMs: Long): ProximityState? {
        latestRssi = rssi
        readings.addLast(Reading(nowMs, rssi))
        prune(nowMs)
        if (rssi >= closeThresholdDbm) lastStrongAt = nowMs
        if (state != ProximityState.NEAR && readings.count { it.rssi >= closeThresholdDbm } >= requiredStrongSamples) {
            state = ProximityState.NEAR
            return state
        }
        return tick(nowMs)
    }

    fun tick(nowMs: Long): ProximityState? {
        prune(nowMs)
        val lastStrong = lastStrongAt
        if (state == ProximityState.NEAR && lastStrong != null && nowMs - lastStrong >= departureDelayMs) {
            state = ProximityState.APART
            return state
        }
        return null
    }

    fun reset() {
        readings.clear()
        state = ProximityState.WAITING
        latestRssi = null
        lastStrongAt = null
    }

    private fun prune(nowMs: Long) {
        while (readings.isNotEmpty() && nowMs - readings.peekFirst().timeMs > stableWindowMs) readings.removeFirst()
    }
}
