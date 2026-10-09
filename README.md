# Струемер Стругацкого / Strugatsky's Streamometer

Игрушка: записывает звук струи с микрофона телефона и рисует кривую потока, время, перерывы и штамп.
A toy: it records the sound of your stream with the phone microphone and draws a flow curve, timing, pauses and a verdict stamp.

Вся обработка идёт в браузере, запись никуда не отправляется. Это не медицинский прибор.
All analysis runs in the browser and the audio is never uploaded. This is not a medical device.

- Русская версия: https://strugatskyl.github.io/struemer/
- English version: https://strugatskyl.github.io/struemer/en/

## Build

`src/struemer.html` is the Russian master. `python3 tools/build.py` writes `index.html` and `en/index.html`;
the English page is produced by the translation table inside `tools/build.py`, and the build fails if any
Russian string is left untranslated.
