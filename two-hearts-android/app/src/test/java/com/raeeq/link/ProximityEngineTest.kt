package com.raeeq.link

import org.junit.Assert.*
import org.junit.Test

class ProximityEngineTest {
    @Test fun noMeetingNeverTriggersDeparture() {
        val engine = ProximityEngine()
        assertNull(engine.tick(50_000L))
        assertEquals(ProximityState.WAITING, engine.state)
    }

    @Test fun threeStrongSamplesConfirmNear() {
        val engine = ProximityEngine()
        assertNull(engine.onRssi(-50, 0L))
        assertNull(engine.onRssi(-52, 500L))
        assertEquals(ProximityState.NEAR, engine.onRssi(-51, 1_000L))
    }

    @Test fun departureRequiresTenSecondsWithoutInRangeSamples() {
        val engine = ProximityEngine()
        engine.onRssi(-50, 0L); engine.onRssi(-51, 500L); engine.onRssi(-52, 1_000L)
        assertNull(engine.tick(10_999L))
        assertEquals(ProximityState.APART, engine.tick(11_000L))
    }

    @Test fun moderateRssiKeepsNearStateAndResetsDepartureTimer() {
        val engine = ProximityEngine()
        engine.onRssi(-50, 0L); engine.onRssi(-51, 500L); engine.onRssi(-52, 1_000L)
        assertNull(engine.onRssi(-61, 5_000L))
        assertNull(engine.tick(14_999L))
        assertEquals(ProximityState.APART, engine.tick(15_000L))
    }

    @Test fun veryWeakReadingsDoNotResetDepartureTimer() {
        val engine = ProximityEngine()
        engine.onRssi(-50, 0L); engine.onRssi(-51, 500L); engine.onRssi(-52, 1_000L)
        assertNull(engine.onRssi(-80, 5_000L))
        assertEquals(ProximityState.APART, engine.tick(11_000L))
    }

    @Test fun closeSamplesReturnToNearAfterDeparture() {
        val engine = ProximityEngine()
        engine.onRssi(-50, 0L); engine.onRssi(-51, 500L); engine.onRssi(-52, 1_000L)
        engine.tick(11_000L)
        engine.onRssi(-50, 12_000L); engine.onRssi(-51, 12_400L)
        assertEquals(ProximityState.NEAR, engine.onRssi(-52, 12_800L))
    }

    @Test fun isolatedStrongSamplesDoNotConfirmNear() {
        val engine = ProximityEngine()
        engine.onRssi(-50, 0L); engine.onRssi(-80, 3_000L); engine.onRssi(-50, 3_500L)
        assertEquals(ProximityState.WAITING, engine.state)
    }
}
