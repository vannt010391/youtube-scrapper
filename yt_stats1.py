from dbm import dumb
from fileinput import filename
import json
import requests
from tqdm import tqdm
import asyncio, sys
import isodate, csv, datetime, os
from bs4 import BeautifulSoup
import pandas as pd


class YTstats:

    def __init__(self, api_key, channel_id):
        self.api_key = api_key
        self.channel_id = channel_id
        self.channel_statistics = None
        self.video_data = None
   

    async def extract_all(self):
        await self.get_channel_statistics()
        await self.get_channel_video_data()

    
            

    async def get_channel_statistics(self):
        """Extract the channel statistics"""
        print('get channel statistics...')
        url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={self.channel_id}&key={self.api_key}'
        pbar = tqdm(total=1)
        
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        try:
            data = data['items'][0]['statistics']
        except KeyError:
            print('Could not get channel statistics')
            data = {}

        self.channel_statistics = data
        pbar.update()
        pbar.close()
        return data

    async def get_channel_video_data(self):
        "Extract all video information of the channel"
        print('get video data...')
        channel_videos, channel_playlists = await self._get_channel_content(limit=50)

        parts=["snippet", "statistics","contentDetails", "topicDetails"]
        for video_id in tqdm(channel_videos):
            for part in parts:
                data = await self._get_single_video_data(video_id, part)
                channel_videos[video_id].update(data)

        self.video_data = channel_videos
        return channel_videos

            

    async def _get_single_video_data(self, video_id, part):
        """
        Extract further information for a single video
        parts can be: 'snippet', 'statistics', 'contentDetails', 'topicDetails'
        """

        url = f"https://www.googleapis.com/youtube/v3/videos?part={part}&id={video_id}&key={self.api_key}"
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        try:
            data = data['items'][0][part]
        except KeyError as e:
            print(f'Error! Could not get {part} part of data: \n{data}')
            data = dict()
        return data

    async def _get_channel_content(self, limit=None, check_all_pages=True):
        """
        Extract all videos and playlists, can check all available search pages
        channel_videos = videoId: title, publishedAt
        channel_playlists = playlistId: title, publishedAt
        return channel_videos, channel_playlists
        """
        url = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={self.channel_id}&part=snippet,id&order=date"
        if limit is not None and isinstance(limit, int):
            url += "&maxResults=" + str(limit)

        vid, pl, npt = await self._get_channel_content_per_page(url)
        idx = 0
        while(check_all_pages and npt is not None and idx < 10):
            nexturl = url + "&pageToken=" + npt
            next_vid, next_pl, npt = await self._get_channel_content_per_page(nexturl)
            vid.update(next_vid)
            pl.update(next_pl)
            idx += 1

        return vid, pl

    async def _get_channel_content_per_page(self, url):
        """
        Extract all videos and playlists per page
        return channel_videos, channel_playlists, nextPageToken
        """
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        channel_videos = dict()
        channel_playlists = dict()
        if 'items' not in data:
            print('Error! Could not get correct channel data!\n', data)
            raise Exception('Error! Could not get correct channel data!')
            #raise Exception('Error! Could not get correct channel data!\n', data)
            return channel_videos, channel_videos, None

        nextPageToken = data.get("nextPageToken", None)

        item_data = data['items']
        for item in item_data:
            try:
                kind = item['id']['kind']
                published_at = item['snippet']['publishedAt']
                title = item['snippet']['title']
                if kind == 'youtube#video':
                    video_id = item['id']['videoId']
                    channel_videos[video_id] = {'publishedAt': published_at, 'title': title}
                elif kind == 'youtube#playlist':
                    playlist_id = item['id']['playlistId']
                    channel_playlists[playlist_id] = {'publishedAt': published_at, 'title': title}
            except KeyError as e:
                print('Error! Could not extract data from item:\n', item)

        return channel_videos, channel_playlists, nextPageToken

    async def dump(self):
        """Dumps channel statistics and video data in a single json file"""
        if self.channel_statistics is None or self.video_data is None:
            print('data is missing!\nCall get_channel_statistics() and get_channel_video_data() first!')
            return

        fused_data = {self.channel_id: {"channel_statistics": self.channel_statistics,
                              "video_data": self.video_data}}

        # channel_title = self.video_data.popitem()[1].get('channelTitle', self.channel_id)
        # channel_title = channel_title.replace(" ", "_").lower()
        # filename = channel_title + '.json'
        filename = self.channel_id + '.json'
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(fused_data, f, indent=4)
        return filename

    async def format_file(self, file):
        outputFile = self.channel_id + '.csv'
        with open(file, 'r', encoding="utf-8") as file:
            file_data = json.load(file)

        values = []
        for item in file_data:
            values.append(file_data[item]['video_data'])

        data = values[0]

        title = ["videoId", "publishedAt","title","channelId","channelTitle","categoryId","liveBroadcastContent","description","viewCount","likeCount","favoriteCount","commentCount","duration","caption","topicCategories","licensedContent","contentRating"]
        with open(outputFile, 'w+', encoding="utf-8") as outputFile:
            cw = csv.DictWriter(outputFile, title)
            cw.writeheader()
            for i, v in enumerate(data):
                data[v].pop("tags", None)
                data[v].pop("defaultAudioLanguage", None)
                data[v].pop("thumbnails", None)
                data[v].pop("tags", None)
                data[v].pop("localized", None)
                data[v].pop("dimension", None)
                data[v].pop("definition", None)
                data[v].pop("projection", None)
                data[v].pop("topicCategories", None)
                data[v].pop("regionRestriction", None)
                data[v].pop("defaultLanguage", None)
                data[v]["videoId"] = list(data)[i]
                data[v]["duration"] = datetime.timedelta(seconds=isodate.parse_duration(data[v]["duration"]).total_seconds())
                data[v]["description"] = str(data[v]["description"]).replace("\n", r"\N")
                cw.writerow(data[v])



async def app(api_key, channel_id) -> None:
    youtube_channel = YTstats(api_key, channel_id)
    await youtube_channel.extract_all()
    file = await youtube_channel.dump()
    await youtube_channel.format_file(file)
    

# channel_id = asyncio.run(getChannelIdFromCustomUrl(sys.argv[2]))
# output = asyncio.run(app(sys.argv[1], channel_id))
output = asyncio.run(app(sys.argv[1], sys.argv[2]))
print(output)

# if __name__ == "__main__":
#     asyncio.run(app())

