import sqlite3


class DB():
    def __init__(self, filename: str):
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()

    def set_new_video_data(self, filename, thumbnail, title, username):
        self.cursor.execute("INSERT INTO videos (filename, thumbnail, title, username) VALUES (?, ?, ?, ?)",
                  (filename, thumbnail, title, username))
        self.connection.commit()

    def get_videos_data(self):
        self.cursor.execute("SELECT * FROM videos")
        data = self.cursor.fetchall()
        return [{'filename': i[1], 'thumbnail': i[2], 'title': i[3], 'username': i[4]} for i in data]

    def __del__(self):
        self.cursor.close()