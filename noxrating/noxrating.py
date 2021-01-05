# ! /usr/bin/env python3

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from progress.bar import Bar
import colorful as cf
import pickle
import csv
import os
import platform

from ranking import Ranking

module_name = "NoxRating: Extract rating of Nox Videos"
__version__ = "0.1.0"


class NoxRating:

    def __init__(self, api_key, ingore_cache, debug):

        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.ranking = Ranking()
        self.export = DataExport()
        self.ignore_cache = ingore_cache
        self.debug = debug

        self.main()

    def print_logo(self):
        cf.print(
            """{c.bold_blue}
            
888b    888                   d8b 
8888b   888                   88P 
88888b  888                   8P  
888Y88b 888  .d88b.  888  888 "   
888 Y88b888 d88""88b `Y8bd8P'     
888  Y88888 888  888   X88K       
888   Y8888 Y88..88P .d8""8b.     
888    Y888  "Y88P"  888  888 {c.reset}{c.purple}    
Spellenzolder - Rating Extractor
            """)

    def get_playlist_id(self):
        """
        Returns the Playlist id of the channel
        :return:
        """

        channels_response = self.youtube.channels().list(
            part='contentDetails',
            forUsername='Dharquen'
        ).execute()

        for channel in channels_response['items']:
            return channel['contentDetails']['relatedPlaylists']['uploads']

        return None

    def get_uploads(self, uploads_playlist_id):
        """
        Returns all the uploads of the given playlist id
        :param uploads_playlist_id:
        """
        # Try to find a cache if exist
        if not self.ignore_cache:
            try:
                with open('../cache/videos.pickle', 'rb') as handle:
                    self.print('Cache found. Disable cache and use API? Use --ignore-cache')
                    return pickle.load(handle)
            except:
                pass

        videos = []
        # Retrieve the list of videos uploaded to the authenticated user's channel.
        playlistitems_list_request = self.youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='snippet',
            maxResults=5
        )

        while playlistitems_list_request:
            playlistitems_list_response = playlistitems_list_request.execute()

            for playlist_item in playlistitems_list_response['items']:
                videos.append({
                    'title': playlist_item['snippet']['title'],
                    'link': 'https://www.youtube.com/watch?v={}'.format(
                        playlist_item['snippet']['resourceId']['videoId']),
                    'id': playlist_item['snippet']['resourceId']['videoId']
                })
            playlistitems_list_request = self.youtube.playlistItems().list_next(
                playlistitems_list_request, playlistitems_list_response)

        # Save Result for caching to save a large amount of API calls
        self.export.save('videos', videos)

        return videos

    def captions(self, uploads):
        """

        :param uploads:
        :return:
        """
        if not self.debug:
            bar = Bar('Processing', max=len(uploads))
        for idx, upload in enumerate(uploads):
            try:
                caption = YouTubeTranscriptApi.get_transcript(upload['id'], ['nl'])
                uploads[idx] = self.ranking.classify_ranking(caption, upload)
                if self.debug:
                    self.print('[debug] {} -> score: {}, {}'.format(uploads[idx]['link'], uploads[idx]['score'],
                                                                    uploads[idx]['id']))
            except Exception as e:
                if self.debug:
                    self.print('[debug] No rating found for video {}'.format(uploads[idx]['link']))
                pass

            if not self.debug:
                bar.next()
        if not self.debug:
            bar.finish()

        return uploads

    def main(self):
        """
        Gathers the Playlist of Nox Youtube Channel
        Finds all the videos NOX has uploaded
        and downloads the Caption
        """
        self.print_logo()

        self.print('Searching for NOX videos.')

        # Get the Playlist ID of all uploads
        playlist_id = self.get_playlist_id()

        # Get list of video's in this playlist
        uploads = self.get_uploads(playlist_id)
        self.print('{} videos found, processing captions for score.'.format(len(uploads)))

        # Download Captions and Rank the captions
        if self.export.exist('uploads') and not self.ignore_cache:
            scored_videos = self.export.load('scored_videos')
        else:
            scored_videos = self.captions(uploads)
            self.export.save('scored_videos', scored_videos)

        self.print('Writing dataset to csv file.')
        self.export.csv(scored_videos)

    def print(self, text):
        print(cf.bold & cf.red | '[noxrating] {}'.format(text))


class DataExport:
    """
    DataExport is responsible for exporting the data to CSV
    and writing the pickle files.
    """

    csv_columns = ['title', 'link', 'id', 'stars', 'score']

    def csv(self, data):
        """

        :param data:
        """
        try:
            with open('dataset.csv', 'w', encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=self.csv_columns, lineterminator='\n')
                writer.writeheader()
                for data in data:
                    print(data)
                    writer.writerow(data)
        except IOError:
            print("I/O error")

    def save(self, name, data):
        """

        :param data:
        :param name:
        """
        with open('../cache/' + name + '.pickle', 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, name):
        """

        :rtype: object
        """
        with open('../cache/' + name + '.pickle', 'rb') as handle:
            return pickle.load(handle)

    def exist(self, name):
        """

        :param name:
        :return:
        """
        return os.path.isfile('../cache/' + name + '.pickle')


def main():
    version_string = f"%(prog)s {__version__}\n" + \
                     f"Python:  {platform.python_version()}"

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=f"{module_name} (Version {__version__})"
                            )
    parser.add_argument("--version",
                        action="version", version=version_string,
                        help="Display version information and dependencies."
                        )

    parser.add_argument("--api-key",
                        dest="api_key",
                        help="Your Youtube API key."
                        )

    parser.add_argument("--ignore-cache", nargs='?',
                        dest="ignore_cache", const=True,
                        help="Ignores the cache build from Youtube API",
                        default=False
                        )

    parser.add_argument("--debug", nargs='?',
                        dest="debug", const=True,
                        help="Your Youtube API key.",
                        default=False
                        )

    args = parser.parse_args()

    NoxRating(args.api_key, args.ignore_cache, args.debug)


if __name__ == "__main__":
    main()
