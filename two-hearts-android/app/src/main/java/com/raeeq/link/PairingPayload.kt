package com.raeeq.link

import java.util.UUID

data class PairingPayload(val sideA: String, val sideB: String) {
    fun encode(): String = "TWOHEARTS|1|$sideA|$sideB"
    fun ownUuid(role: String): UUID = UUID.fromString(if (role == "A") sideA else sideB)
    fun partnerUuid(role: String): UUID = UUID.fromString(if (role == "A") sideB else sideA)

    companion object {
        fun create() = PairingPayload(UUID.randomUUID().toString(), UUID.randomUUID().toString())
        fun parse(raw: String): PairingPayload? {
            val parts = raw.trim().split('|')
            if (parts.size != 4 || parts[0] != "TWOHEARTS" || parts[1] != "1") return null
            val a = runCatching { UUID.fromString(parts[2]).toString() }.getOrNull() ?: return null
            val b = runCatching { UUID.fromString(parts[3]).toString() }.getOrNull() ?: return null
            if (a == b) return null
            return PairingPayload(a, b)
        }
    }
}
