"""
NoxRating classifier
"""
import numpy as np
import re


class Ranking:
    match = [
        '2',
        '3',
        '4',
        '5',
        '6',
        '7',
        '8',
        '9',
        '10'
    ]

    numbers_in_full = {
        'twee': '2',
        'drie': '3',
        'vier': '4',
        'vijf': '5',
        'zes': '6',
        'zeven': '7',
        'acht': '8',
        'negen': '9',
        'tien': '10',

        # Known faults in subtitles mechanics
        'zever': '7',
    }

    def classify_ranking(self, captions, upload):
        """
        Does a series of task to classify the rating of the given caption.

        Captions comes in multiple objects [{text: ..}{..}{..}]
        Each object is a sentence with a start and duration.
        :rtype: object
        """

        # Only grab text and concat everything, from these caption objects
        caption = ' '.join([elem['text'] for elem in captions])

        score = self.get_score(caption)

        if 'sterren' in caption and score * 2 <= 10:
            upload['score'] = score * 2
            upload['stars'] = score
        else:
            upload['score'] = score

        return upload

    def get_score(self, caption, debug=False):
        """
        The scoring part has it's own function for testing purposes.

        :param caption:
        :param debug:
        """
        # Remove first 95%, this is not needed because the score is given in the last minutes
        skip = int(np.ceil(0.95 * len(caption.split())))
        caption = ' '.join(caption.split(' ')[skip:])

        # Replace 'tien' with '10'
        # This makes it also possible to replace 'wacht' with 'w8'. This is good, since
        # The Caption system sometimes translates '8' into 'wacht' because of pronounciation.
        for key in self.numbers_in_full.keys():
            caption = caption.replace(key, self.numbers_in_full[key])

        # Get the last number that is in the caption.
        numbers = re.findall(r'[2-9]|10', caption)
        if debug:
            print('[debug] Following numbers found: {}'.format(numbers))
        score = numbers[-1]

        return int(score)


if __name__ == "__main__":
    from youtube_transcript_api import YouTubeTranscriptApi

    test_id = 'ycqrJy2988c'
    captions = YouTubeTranscriptApi.get_transcript(test_id, ['nl'])

    caption = ' '.join([elem['text'] for elem in captions])

    ranking = Ranking()
    print(ranking.get_score(caption, True))
