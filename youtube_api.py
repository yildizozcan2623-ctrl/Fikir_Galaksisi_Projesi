import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_top_comments(video_id, max_comments=3):
    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_comments,
            order="relevance",
            textFormat="plainText"
        ).execute()

        comments = []
        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            if len(top_comment) > 150:
                top_comment = top_comment[:150] + "..."
            comments.append(top_comment)

        return comments
    except Exception as e:
        print(f"Yorum çekme hatası: {e}")
        return []

def get_video_details(video_ids):
    """Video detaylarını çek"""
    if not video_ids:
        return []

    try:
        response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids)
        ).execute()

        results = []
        for item in response.get("items", []):
            results.append({
                "id": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "channel": item["snippet"]["channelTitle"],
                "likeCount": int(item["statistics"].get("likeCount", 0)),
                "commentCount": int(item["statistics"].get("commentCount", 0)),
                "viewCount": int(item["statistics"].get("viewCount", 0)),
                "duration": item["contentDetails"]["duration"]
            })

        return results
    except Exception as e:
        print(f"Video detay API hatası: {e}")
        return []