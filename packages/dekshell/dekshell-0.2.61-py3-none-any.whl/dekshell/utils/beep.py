from dekmedia.audio.core import play_res


def sound_notify(success):
    play_res('success' if success else 'failure')
