#pyinstaller --onefile --add-data "correct.wav:." --add-data "wrong.wav:." --add-data "NotoSansSC-Regular.ttf:." jeopardy.py
#
#pyinstaller --onefile \
#  --add-binary "/full/path/SDL2-2.0.26.dylib:." \
#  --add-data "correct.wav:." \
#  --add-data "wrong.wav:." \
#  --add-data "NotoSansSC-Regular.ttf:." \
#  jeopardy.py

pyinstaller --onefile \
  --add-data "correct.wav:." \
  --add-data "wrong.wav:." \
  --add-data "NotoSansSC-Regular.ttf:." \
  --add-data "q*.txt:." \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/base.cpython-310-darwin.so:pygame" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/display.cpython-310-darwin.so:pygame" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/mixer.cpython-310-darwin.so:pygame" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/_sdl2/audio.cpython-310-darwin.so:pygame/_sdl2" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/_sdl2/controller.cpython-310-darwin.so:pygame/_sdl2" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/_sdl2/mixer.cpython-310-darwin.so:pygame/_sdl2" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/_sdl2/sdl2.cpython-310-darwin.so:pygame/_sdl2" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/_sdl2/touch.cpython-310-darwin.so:pygame/_sdl2" \
  --add-binary "/Users/huw/anaconda3/envs/game/lib/python3.10/site-packages/pygame/_sdl2/video.cpython-310-darwin.so:pygame/_sdl2" \
  jeopardy.py

