package com.raeeq.link

import java.util.UUID

data class PairingPayload(
    val sideA: String,
    val sideB: String,
    val receiverRole: String? = null
) {
    fun encode(): String = "TWOHEARTS|1|$sideA|$sideB"

    fun encodeForReceiverRole(role: String): String {
        require(role == "A" || role == "B") { "Receiver role must be A or B" }
        return "TWOHEARTS|2|$sideA|$sideB|$role"
    }

    fun ownUuid(role: String): UUID = UUID.fromString(if (role == "A") sideA else sideB)
    fun partnerUuid(role: String): UUID = UUID.fromString(if (role == "A") sideB else sideA)

    companion object {
        fun create() = PairingPayload(UUID.randomUUID().toString(), UUID.randomUUID().toString())

        fun parse(raw: String): PairingPayload? {
            val parts = raw.trim().split('|')
            if (parts.firstOrNull() != "TWOHEARTS") return null

            val receiverRole = when (parts.getOrNull(1)) {
                "1" -> {
                    if (parts.size != 4) return null
                    null
                }
                "2" -> {
                    if (parts.size != 5 || (parts[4] != "A" && parts[4] != "B")) return null
                    parts[4]
                }
                else -> return null
            }

            val a = runCatching { UUID.fromString(parts[2]).toString() }.getOrNull() ?: return null
            val b = runCatching { UUID.fromString(parts[3]).toString() }.getOrNull() ?: return null
            if (a == b) return null
            return PairingPayload(a, b, receiverRole)
        }
    }
}
