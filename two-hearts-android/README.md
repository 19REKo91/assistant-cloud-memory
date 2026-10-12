# Link — offline two-phone proximity prototype

A small native Android prototype for two Android 12+ phones. Pair once by scanning a QR code, then activate the experience on both phones. Each phone advertises one random, pair-specific BLE service UUID and scans only for the other phone's UUID. No GATT connection, internet, server, account, GPS, remote asset transfer, or background service is used.

## Prototype behavior

- One QR scan completes local pairing on the second phone.
- Both phones must be activated in the app to start the experience.
- Three strong readings inside a rolling 2.5-second window establish the near state.
- After a meeting, 10 seconds without another sufficiently strong reading switches to the apart state.
- Later stable close readings return to the near state.
- Emoji, a pulse animation, and short system tones are placeholders for the final images and music.
- Long-press the LINK heading to reveal current RSSI for a controlled check.

## Limitations

RSSI is a noisy proximity indicator, not a reliable physical-contact or centimeter-distance sensor. Phone position, hands/bodies, cases and the room affect readings. The default threshold is -56 dBm and may need one controlled adjustment for these phones. Android runtime permissions and BLE advertising/scanning support are checked at run time. The app must stay in the foreground on both phones.

This prototype uses Android BLE advertisement and scan APIs directly and does not copy implementation code from the reviewed projects.
