package com.raeeq.link

import org.junit.Assert.*
import org.junit.Test

class PairingPayloadTest {
    @Test fun generatedPairRoundTripsAndUsesDifferentIds() {
        val payload = PairingPayload.create()
        val parsed = PairingPayload.parse(payload.encode())
        assertNotNull(parsed)
        assertEquals(payload.sideA, parsed?.sideA)
        assertEquals(payload.sideB, parsed?.sideB)
        assertNull(parsed?.receiverRole)
        assertNotEquals(payload.sideA, payload.sideB)
    }

    @Test fun transferQrPreservesIdsAndAssignsReceiverRole() {
        val payload = PairingPayload.create()
        for (receiverRole in listOf("A", "B")) {
            val parsed = PairingPayload.parse(payload.encodeForReceiverRole(receiverRole))
            assertNotNull(parsed)
            assertEquals(payload.sideA, parsed?.sideA)
            assertEquals(payload.sideB, parsed?.sideB)
            assertEquals(receiverRole, parsed?.receiverRole)
        }
    }

    @Test fun malformedAndDuplicateIdsAreRejected() {
        assertNull(PairingPayload.parse("not a pair"))
        assertNull(PairingPayload.parse("TWOHEARTS|1|00000000-0000-0000-0000-000000000001|00000000-0000-0000-0000-000000000001"))
        assertNull(PairingPayload.parse("TWOHEARTS|2|00000000-0000-0000-0000-000000000001|00000000-0000-0000-0000-000000000002|C"))
    }
}
