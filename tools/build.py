#!/usr/bin/env python3
"""Build the hosted pages from src/struemer.html (the Russian master, in Claude-artifact format:
<title>, <link>, <style>, then body content).

    index.html       Russian page
    en/index.html    English page

The English page is the master with every Russian string swapped through the EN table below.
The build fails loudly if a table entry is not found the expected number of times, or if a single
Cyrillic letter survives in the English output, so a string added to the master cannot ship
untranslated. Locale behaviour (number format, plurals, fluid ounces) is switched by the LOC line.

Run:  python3 tools/build.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "struemer.html"
SITE = "https://strugatskyl.github.io/struemer/"

# (russian, english[, expected count]); applied longest first.
EN = [
    # ---- head and header
    ("<title>Струемер Стругацкого</title>", "<title>Strugatsky’s Streamometer</title>"),
    ("Акустическая урофлоуметрия на коленке · собрано с Claude", "Garage-built acoustic uroflowmetry · made with Claude"),
    ('<a class="lang" href="https://strugatskyl.github.io/struemer/en/" hreflang="en">EN</a>',
     '<a class="lang" href="https://strugatskyl.github.io/struemer/" hreflang="ru">RU</a>'),
    ("<h1>Струемер Стругацкого</h1>", "<h1>Strugatsky’s Streamometer</h1>"),
    ("Раньше к напору прислушивалась мама. Теперь я. Жми жёлтую кнопку. Диагнозов не ставлю.",
     "Your watch tracks your steps, your sleep and your stress. I track the one thing it won’t. Hit the yellow button. No diagnoses, just data and a laugh."),

    # ---- new reading
    ('id="h-measure">Новый замер</h2>', 'id="h-measure">New reading</h2>'),
    ("</span>Записать</button>", "</span>Record</button>"),
    ('id="pick">Выбрать запись</button>', 'id="pick">Choose a recording</button>'),
    ('aria-label="Идёт запись"', 'aria-label="Recording"'),
    ('id="rec-stop">Стоп</button>', 'id="rec-stop">Stop</button>'),
    ("Нажми, положи телефон на бачок, пару секунд помолчи и начинай. «Стоп» жми до смыва.",
     "Tap, set the phone on the toilet tank, give it two quiet seconds, then go. Hit Stop before you flush."),
    ("Запиши процесс на диктофон телефона, останови запись до смыва и выбери файл здесь.",
     "Record it with your phone’s voice recorder, stop before you flush, then choose the file here."),
    ('Запись в одно нажатие, прямо с микрофона, работает в версии на <a href="https://strugatskyl.github.io/struemer/" target="_blank" rel="noopener">strugatskyl.github.io/struemer</a>.',
     'One-tap recording straight from the microphone works in the version at <a href="https://strugatskyl.github.io/struemer/en/" target="_blank" rel="noopener">strugatskyl.github.io/struemer/en</a>.'),
    ("Как записать, чтобы вышло точнее", "How to get a cleaner reading"),
    ("Включи диктофон и положи телефон на бачок или полку рядом. Шумоподавление в диктофоне выключи, если оно есть.",
     "Start your voice recorder and set the phone on the toilet tank or a nearby shelf. Turn off noise reduction in the recorder if it has one."),
    ("Подожди две-три секунды тишины и начинай. Целься в воду: звук даёт вода, а не фаянс.",
     "Wait two or three quiet seconds, then go. Aim for the water: the sound comes from the water, not the porcelain.", 2),
    ("Закончил, ещё пара секунд тишины, стоп. Смывать после остановки записи.",
     "When you’re done, give it two more quiet seconds, then stop. Flush after the recording is stopped."),
    ("Выбери файл записи здесь.", "Choose the recording file here."),
    ("Нажми «Записать», разреши доступ к микрофону и положи телефон на бачок или полку рядом.",
     "Tap Record, allow microphone access, and set the phone on the toilet tank or a nearby shelf."),
    ("Закончил, ещё пара секунд тишины, «Стоп». Смывать после.",
     "When you’re done, two more quiet seconds, then Stop. Flush afterward."),

    # ---- result
    ('id="h-result">Результат</h2>', 'id="h-result">Result</h2>'),
    ('id="tag">Пример</span>', 'id="tag">Sample</span>'),
    ('aria-label="Сцена: струя заливает мишень"', 'aria-label="Scene: the stream floods a target"'),
    ('<legend class="label">Мишень</legend>', '<legend class="label">Target</legend>'),
    ("Будильник <small>150 мл · 10 с</small>", "Alarm clock <small>5 oz · 10 s</small>"),
    ("Костёр <small>300 мл · 20 с</small>", "Campfire <small>10 oz · 20 s</small>"),
    ("Обещалкин <small>450 мл · 30 с</small>", "Mr. Promises <small>15 oz · 30 s</small>"),
    ("Показать мультик", "Play the cartoon"),
    ("Мишень считается залитой по миллилитрам, если объём известен, иначе по секундам потока. Обещалкин — выдуманный кандидат, все совпадения случайны.",
     "A target counts as flooded by ounces when the volume is known, otherwise by seconds of flow. Mr. Promises is fictional. Any resemblance to your boss, your contractor or your elected officials is coincidental."),
    ("<h3>Перед сохранением</h3>", "<h3>Before you save</h3>"),
    ('<span class="label">Объём, мл</span>', '<span class="label">Volume, fl oz</span>'),
    ('inputmode="numeric" min="20" max="1500" step="10" placeholder="если мерил"',
     'inputmode="decimal" min="1" max="50" step="0.5" placeholder="if measured"'),
    ('<legend class="label">Время суток</legend>', '<legend class="label">Time of day</legend>'),
    ("<span>Утро</span>", "<span>Morning</span>"),
    ("<span>День</span>", "<span>Midday</span>"),
    ("<span>Вечер</span>", "<span>Evening</span>"),
    ("> Мой туалет, телефон на обычном месте</label>", "> My usual bathroom, phone in its usual spot</label>"),
    ("Объём необязателен. Если писал в мерный стакан, впиши миллилитры: посчитаю мл/с и засчитаю замер в личную калибровку. Галочку сними, если писал не там, где обычно.",
     "Volume is optional. If you used a measuring cup, enter the ounces: I’ll work out mL/s and count this reading toward your personal calibration. Uncheck the box if this wasn’t your usual bathroom."),
    ('id="save" hidden>Сохранить в журнал</button>', 'id="save" hidden>Save to logbook</button>'),
    ('id="again">Новый замер</button>', 'id="again">New reading</button>'),
    ("Это пример: так выглядит результат. Свои замеры можно будет сохранять в журнал.",
     "This is a sample result. Your own readings can be saved to the logbook."),
    ('for="w-start">Начало <output', 'for="w-start">Start <output'),
    ('for="w-end">Конец <output', 'for="w-end">End <output'),
    ("Границы ставлю сам. Если в запись попал смыв или хлопок крышки, подвинь.",
     "I set the boundaries automatically. If a flush or a slammed lid made it into the recording, drag them."),

    # ---- calibration, logbook, trust
    ('id="h-cal">Личная калибровка</h2>', 'id="h-cal">Personal calibration</h2>'),
    ("Разброс большой. Скорее всего, телефон лежит по-разному или диктофон сам подкручивает громкость. Клади телефон в одно и то же место и выключи автоусиление, если оно есть.",
     "The spread is large. Most likely the phone sits in a different spot each time, or the recorder is adjusting volume on its own. Keep the phone in the same place and turn off auto gain if you can."),
    ("Калибровка действует там, где набрана: тот же туалет, телефон на том же месте. В зачёт идут замеры со стаканом от 100 мл, последние двадцать.",
     "Calibration only holds where it was built: same bathroom, phone in the same spot. It uses your last twenty measuring-cup readings of 3.5 oz (100 mL) or more."),
    ('id="h-log">Журнал</h2>', 'id="h-log">Logbook</h2>'),
    ("Открываю журнал…", "Opening the logbook…", 3),
    ('id="h-trust">Чему тут верить</h2>', 'id="h-trust">What to trust</h2>'),
    ("Времени, форме кривой и перерывам верить можно. Это микрофон слышит хорошо.",
     "Timing, curve shape and pauses are solid. A microphone hears those well."),
    ("Миллилитрам в секунду верить осторожно. Они получаются из объёма (стакан или личная калибровка) и допущения, что громкость пропорциональна потоку. Калибровка честно показывает свой разброс.",
     "Take the mL/s numbers with a grain of salt. They come from volume (a measuring cup or your personal calibration) plus the assumption that loudness tracks flow. The calibration shows its own spread so you can judge it."),
    ("Сравнивать замеры между собой стоит только в одном и том же туалете, с телефоном на одном и том же месте.",
     "Only compare readings taken in the same bathroom with the phone in the same spot."),
    ("Про простату звук не говорит ничего. Слабая струя бывает по многим причинам, а ранний рак простаты струю обычно не меняет.",
     "Sound says nothing about your prostate. A weak stream has many possible causes, and early prostate cancer usually doesn’t change the stream at all."),
    ("Мишени тем более ничего не значат. Это игра.", "The targets mean even less. They’re a game."),
    ("Когда идти к урологу, а не к Струемеру", "When to see a urologist instead of a Streamometer"),
    ("Слабая или прерывистая струя держится неделями. Встаёшь ночью два раза и чаще. Кровь в моче, боль или жжение. Не получается помочиться совсем: это срочно, в тот же день.",
     "A weak or stop-and-go stream that lasts for weeks. Getting up twice or more a night. Blood in your urine, pain or burning. Can’t go at all: that is urgent, get care the same day."),
    ("Для масштаба: млекопитающие тяжелее 3 кг опорожняют пузырь в среднем за 21 секунду, плюс-минус 13 (Yang et al., PNAS, 2014). Струемер это игрушка, а не медицинский прибор.",
     "For scale: mammals over about 7 pounds empty their bladders in 21 seconds on average, give or take 13 (Yang et al., PNAS, 2014; yes, it won an Ig Nobel). Streamometer is a toy. It is not a medical device and not medical advice."),

    # ---- script: locale and vocabulary
    ("const LOC = { lang: 'ru', num: 'ru-RU', oz: false };", "const LOC = { lang: 'en', num: 'en-US', oz: true };"),
    ("{ morning: 'Утро', day: 'День', evening: 'Вечер' }", "{ morning: 'Morning', day: 'Midday', evening: 'Evening' }"),
    ("'Не расслышал'", "'Couldn’t hear you'"),
    ("'Мало налито'", "'Not much in the tank'"),
    ("'С перерывами'", "'Stop-and-go'"),
    ("'Напор годный'", "'Good to go'"),
    ("'Напор так себе'", "'Middle of the road'"),
    ("'Напор слабый'", "'Low pressure'"),
    ("'Долго'", "'Taking your time'"),
    ("'С заминкой'", "'One hiccup'"),
    ("'Плато'", "'Plateau'"),
    ("'Форма в норме'", "'Textbook curve'"),
    ("'Будильник'", "'Alarm clock'"),
    ("'Костёр'", "'Campfire'"),
    ("'Обещалкин'", "'Mr. Promises'"),
    ("plural(n, 'раз', 'раза', 'раз')", "plural(n, 'time', 'times', 'times')"),
    ("'замер', 'замера', 'замеров'", "'reading', 'readings', 'readings'", 2),

    # ---- script: verdicts
    ("'В записи не слышно тишины до и после. Начало и конец могли обрезаться, проверь границы.'",
     "'I can’t hear any silence before or after. The start and end may be clipped, so check the boundaries.'"),
    ("'Струю почти не слышно. Положи телефон ближе, целься в воду и запиши ещё раз.'",
     "'I can barely hear the stream. Move the phone closer, aim for the water and try again.'"),
    ("'По личной калибровке вышло около '", "'Your personal calibration puts this at about '"),
    ("'Объём '", "'Volume: '"),
    ("' При объёме меньше 150 мл кривую не оценивают даже в клинике. Приходи с полным пузырём.'",
     "' Under about 5 oz (150 mL), even a clinic won’t read much into the curve. Come back with a full tank.'"),
    ("'Струя прерывалась '", "'The stream paused '"),
    ("'. Разово бывает у всех: отвлёкся, тужился, сменил прицел. Если так в каждом замере, покажи журнал урологу.'",
     "'. It happens to everyone now and then: you got distracted, pushed, or changed your aim. If it shows up in every reading, show your logbook to a urologist.'"),
    ("'По личной калибровке Qmax около '", "'Per your personal calibration, Qmax is about '"),
    ("'Оценка Qmax '", "'Estimated Qmax: '"),
    ("' мл/с.'", "' mL/s.'", 2),
    ("' Ориентир для мужчин при объёме от 150 мл: выше 15 считается нормой.'",
     "' The usual rule of thumb for men voiding at least 5 oz (150 mL): above 15 is considered normal.'"),
    ("' Это серая зона от 10 до 15. Смотри на тренд по журналу, а не на один замер.'",
     "' That’s the gray zone between 10 and 15. Watch the trend in your logbook, not a single reading.'"),
    ("' Это ниже 10. Один замер ничего не доказывает: микрофон и диктофон могли соврать. Повтори несколько раз на полном пузыре. Если повторяется, покажи журнал урологу, там измерят прибором.'",
     "' That’s under 10. One reading proves nothing: the microphone may be off. Repeat it a few times with a full bladder. If it keeps showing up, take your logbook to a urologist, who can measure it with a real device.'"),
    ("'Была одна пауза посреди струи.'", "'There was one pause mid-stream.'"),
    ("' секунд. Это либо очень полный пузырь, либо слабый поток, по звуку не отличить. Измерь объём мерным стаканом, тогда посчитаю мл/с.'",
     "' seconds. Either a very full bladder or a slow flow; sound alone can’t tell which. Measure the volume with a cup and I’ll work out mL/s.'"),
    ("'Одна пауза посреди струи. Сама по себе ничего не значит. Интересно, повторится ли.'",
     "'One pause mid-stream. On its own it means nothing. Worth seeing if it repeats.'"),
    ("'Кривая длинная и плоская, без выраженного пика. Так бывает при сужении на выходе, а бывает из-за шумоподавления в диктофоне. Измерь объём, чтобы получить мл/с.'",
     "'The curve is long and flat with no clear peak. That can come from a narrowing downstream, or just from your phone’s noise reduction. Measure the volume to get mL/s.'"),
    ("'Кривая поднимается, держится и спадает без провалов. Напор в мл/с не скажу, пока не укажешь объём.'",
     "'The curve rises, holds and tapers with no dips. I can’t give you mL/s until you enter a volume.'"),
    ("'Мл/с посчитаны без стакана, по личной калибровке: '", "'mL/s estimated without a cup, from your personal calibration: '"),
    ("', разброс ±'", "', spread ±'", 2),
    ("'Калибровка предсказала бы '", "'Calibration would have predicted '"),
    ("', в стакане '", "', your cup says '"),
    ("'. Расхождение '", "'. Off by '"),

    # ---- script: readout
    ("'так выглядит результат · кривая синтетическая, 320 мл'", "'sample result · synthetic curve, about 11 oz'"),
    ("'<small>нужен объём</small>'", "'<small>needs a volume</small>'"),
    ("'Время мочеиспускания'", "'Voiding time'"),
    ("'Время потока'", "'Flow time'"),
    ("'До максимума'", "'Time to peak'"),
    ("'Перерывы'", "'Pauses'"),
    ("'Объём'", "'Volume'"),
    ("' <small>калибровка</small>'", "' <small>calibration</small>'"),
    ("' <small>мл/с</small>'", "' <small>mL/s</small>'", 2),
    ("'Сохранено'", "'Saved'"),
    ("'Сохранить в журнал'", "'Save to logbook'"),

    # ---- script: scene
    ("'Обещаю!'", "'Trust me!'"),
    ("'Э-э…'", "'Uh…'"),
    ("'пшшш'", "'tssss'"),
    ("'буль'", "'glub'"),
    ("'Залито '", "'Flooded '"),
    ("'Мишень сухая. Нужна запись, на которой слышно струю.'", "'The target is dry. I need a recording where the stream is audible.'"),
    ("'около '", "'about '"),
    ("' с потока'", "' s of flow'", 2),
    ("'Будильник утоплен и больше не звонит: '", "'The alarm clock is underwater and done ringing: '"),
    ("'Будильник отзвонил своё: залито '", "'The alarm clock rang on: flooded '"),
    ("'Костёр потушен, лес спасён: '", "'The campfire is out and the forest is safe: '"),
    ("'Костёр ещё дымит: залито '", "'The campfire is still smoking: flooded '"),
    ("'Обещалкин залит по шляпу: '", "'Mr. Promises is in over his hat: '"),
    ("'. Прогноз Струемера: выборы он проиграл.'", "'. He promises it never happened.'"),
    ("'Обещалкин устоял: залито '", "'Mr. Promises is still talking: flooded '"),
    ("'. Прогноз Струемера: второй тур.'", "'. He promises you’ll get him next time.'"),
    ("' при норме '", "' against a par of '", 3),
    ("'%, нужно '", "'%, needs '", 3),
    ("'Сцена с мишенью. '", "'Target scene. '"),

    # ---- script: chart
    ("'мл/с' : 'отн. ед.'", "'mL/s' : 'rel. units'"),
    (">секунды</text>", ">seconds</text>"),
    ("' мл/с' : 'пик'", "' mL/s' : 'peak'"),
    ("'Кривая потока. Время мочеиспускания '", "'Flow curve. Voiding time '"),
    ("' с, перерывов: '", "' s, pauses: '"),
    ("' с · '", "' s · '"),

    # ---- script: logbook and calibration
    ("'Журнал хранится в твоём аккаунте, виден только тебе и открывается с любого устройства. Сама запись никуда не отправляется: её разбирает браузер, в журнал идут только цифры и форма кривой.'",
     "'Your logbook lives in your account, is visible only to you, and opens on any device. The audio itself is never uploaded: your browser analyzes it, and only the numbers and the curve shape are saved.'"),
    ("'Журнал хранится только в этом браузере. Сама запись никуда не отправляется: её разбирает браузер.'",
     "'Your logbook is stored only in this browser. The audio never leaves your phone: your browser does all the analysis. No account, no ads.'"),
    ("'Журнал сейчас недоступен. Новые замеры не сохранятся, пока не обновишь страницу.'",
     "'The logbook is unavailable right now. New readings won’t be saved until you reload the page.'"),
    ("'Замеров со стаканом: '", "'Cup readings: '", 2),
    ("' из '", "' of '", 2),
    ("'Струемер подстраивается под твой унитаз и твой телефон. Десять замеров со стаканом, и дальше он считает мл/с сам, без стакана. Черновая оценка появится уже после третьего.'",
     "'Streamometer tunes itself to your bathroom and your phone. Ten readings with a measuring cup, and from then on it estimates mL/s by itself, no cup needed. A rough estimate kicks in after the third.'"),
    ("'Ещё один'", "'One more'"),
    ("'Ещё два'", "'Two more'"),
    ("', и появится черновая оценка мл/с без стакана.'", "', and you get a rough mL/s estimate without a cup.'"),
    ("'Черновая калибровка работает'", "'Draft calibration is live'"),
    ("'. Мл/с без стакана уже считаются, каждый следующий стакан делает их точнее.'",
     "'. You now get mL/s without a cup, and every extra cup reading sharpens it.'"),
    ("'Калибровка набрана'", "'Calibration complete'"),
    ("'. Стакан больше не обязателен. Новые замеры со стаканом продолжают её уточнять.'",
     "'. The cup is now optional. New cup readings keep refining it.'"),
    ("Пока пусто. Каждый сохранённый замер встанет сюда строкой: дата, кривая, время и штамп. Через неделю будет видно, чем утро отличается от вечера.",
     "Nothing here yet. Each saved reading lands here as a row: date, curve, time and stamp. Give it a week and you’ll see how mornings differ from evenings."),
    ("' с</span><span>'", "' s</span><span>'"),
    ("' мл/с' : 'без объёма'", "' mL/s' : 'no volume'"),
    (">Удалить</button>", ">Delete</button>"),
    ("'Удалить'", "'Delete'"),
    ("'Точно удалить?'", "'Really delete?'"),
    ('<th scope="col">Медианы</th><th scope="col">Замеров</th><th scope="col">Время</th>',
     '<th scope="col">Medians</th><th scope="col">Readings</th><th scope="col">Time</th>'),

    # ---- script: messages
    ("'Не сохранилось. На этой странице у тебя нет права записи в журнал.'", "'Not saved. You don’t have permission to write to this logbook.'"),
    ("'Не сохранилось: журнал переполнен. Удали старые замеры.'", "'Not saved: the logbook is full. Delete some old readings.'"),
    ("'Не сохранилось: браузер не даёт записать данные. Проверь, не приватное ли это окно.'",
     "'Not saved: the browser won’t store data. Check whether this is a private window.'"),
    ("'Не сохранилось: журнал сейчас недоступен. Попробуй ещё раз через минуту.'",
     "'Not saved: the logbook is unavailable right now. Try again in a minute.'"),
    ("'Не удалилось: журнал сейчас недоступен.'", "'Not deleted: the logbook is unavailable right now.'"),
    ("'Слушаю запись…'", "'Listening…'"),
    ("'Не смог прочитать этот файл. Подойдут m4a, mp3, wav, ogg. Если диктофон пишет в amr или 3gp, поменяй формат в его настройках.'",
     "'I couldn’t read that file. m4a, mp3, wav and ogg work. If your recorder saves amr or 3gp, change the format in its settings.'"),
    ("'Запись короче трёх секунд. Тут нечего мерить.'", "'That recording is under three seconds. Nothing to measure.'"),
    ("'Запись длиннее пяти минут. Обрежь её до самого процесса.'", "'That recording is over five minutes. Trim it down to the main event.'"),
    ("'Этот браузер не умеет разбирать звук. Открой страницу в Chrome или Safari.'", "'This browser can’t decode audio. Open the page in Chrome or Safari.'"),
    ("'Не получилось разобрать запись. Попробуй другой файл.'", "'I couldn’t analyze that recording. Try another file.'"),
    ("'Микрофон не разрешён. Разреши этому сайту доступ к микрофону в настройках браузера и нажми ещё раз.'",
     "'Microphone access is blocked. Allow this site to use the microphone in your browser settings, then tap again.'"),
    ("'Микрофон не найден.'", "'No microphone found.'"),
    ("'Не получилось включить микрофон. Запиши на диктофон и выбери файл.'", "'I couldn’t start the microphone. Use your voice recorder and choose the file instead.'"),
    ("'Этот браузер не умеет записывать звук. Запиши на диктофон и выбери файл.'", "'This browser can’t record audio. Use your voice recorder and choose the file instead.'"),
    ("'Запись с микрофона'", "'Microphone recording'"),
    ("'Телефон не дал выключить автоусиление микрофона. Форма и время верны, а личная калибровка будет шумнее.'",
     "'Your phone wouldn’t turn off automatic gain. Shape and timing are still right, but personal calibration will be noisier.'"),
    ("'или выбрать готовую запись'", "'or choose an existing recording'"),

    # ---- units (shortest, so they go last)
    ("' мл/с'", "' mL/s'", 3),
    ("' мл'", "' mL'", 2),
    ("' с'", "' s'", 6),
]

HEAD = {
    "ru": {
        "lang": "ru",
        "description": "Телефон слушает струю и рисует кривую потока, время, перерывы и штамп. Игрушка, не медицинский прибор.",
        "url": SITE,
        "image": None,
    },
    "en": {
        "lang": "en",
        "description": "Your phone listens, draws your flow curve, and helps you drown a cartoon alarm clock. A garage-built take on acoustic uroflowmetry. A toy, not a medical device.",
        "url": SITE + "en/",
        "image": SITE + "en/og.png",
    },
}

CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def translate(src: str) -> str:
    out = src
    for entry in sorted(EN, key=lambda e: -len(e[0])):
        ru, en = entry[0], entry[1]
        want = entry[2] if len(entry) > 2 else 1
        got = out.count(ru)
        if got != want:
            sys.exit(f"EN table: expected {want} of {ru[:70]!r}, found {got}")
        out = out.replace(ru, en)
    left = sorted({m.group(0) for m in CYRILLIC.finditer(out)})
    if left:
        line = next(l for l in out.splitlines() if CYRILLIC.search(l))
        sys.exit(f"Untranslated Russian left in the English page ({''.join(left)}), e.g.: {line.strip()[:160]}")
    return out


def wrap(page: str, key: str) -> str:
    """Turn the artifact-format page into a complete standalone HTML document."""
    m = re.match(r"\s*<title>(.*?)</title>\s*(<link[^>]*>)\s*(<style>.*?</style>)\s*(.*)\Z", page, re.S)
    if not m:
        sys.exit("src/struemer.html must start with <title>, <link>, <style>")
    title, link, style, body = m.groups()
    h = HEAD[key]
    og = [
        f'<meta name="description" content="{h["description"]}">',
        f'<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{h["description"]}">',
        f'<meta property="og:url" content="{h["url"]}">',
    ]
    if h["image"]:
        og += [
            f'<meta property="og:image" content="{h["image"]}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="627">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]
    return "\n".join([
        "<!doctype html>",
        f'<html lang="{h["lang"]}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
        '<meta name="robots" content="noindex,nofollow">',
        f"<title>{title}</title>",
        *og,
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        link,
        "<style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}img{max-width:100%}</style>",
        style,
        "</head>",
        "<body>",
        body.strip(),
        "</body>",
        "</html>",
        "",
    ])


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    en = translate(src)
    (ROOT / "index.html").write_text(wrap(src, "ru"), encoding="utf-8")
    (ROOT / "en").mkdir(exist_ok=True)
    (ROOT / "en" / "index.html").write_text(wrap(en, "en"), encoding="utf-8")
    # the English page in artifact format, for tests and previews
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out:
        out.write_text(en, encoding="utf-8")
    print(f"built index.html and en/index.html from {SRC.relative_to(ROOT)} ({len(EN)} strings)")


if __name__ == "__main__":
    main()
