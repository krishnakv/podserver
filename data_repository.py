import psycopg2

from models import Episode


class DataRepository:
    def __init__(self, config):
        self.config = config

    def get_episodes(self, pid):
        conn = self._get_conn()

        cur = conn.cursor()

        pid = 1
        print("going to fetch episodes")
        cur.execute(
            f"SELECT id, episodeid, title, summary, transcript, questions FROM episodes WHERE podcastid = {pid} and transcribed=true ORDER BY episodeid DESC LIMIT 15;"
        )
        print("fetched episodes")
        rows = cur.fetchall()
        print("rows fetched")

        episodes = []
        for row in rows:
            episode = Episode(row[1], row[2], row[3], row[4], row[5])
            # print(episode)
            episodes.append(episode)

        cur.close()
        conn.close()

        return episodes

    def get_episode(self, pid, eid):
        conn = self._get_conn()

        cur = conn.cursor()

        pid = 1
        cur.execute(
            f"SELECT id, episodeid, title, summary, transcript, questions FROM episodes WHERE podcastid = {pid} and episodeid = {eid} and transcribed=true ORDER BY episodeid DESC;"
        )
        row = cur.fetchone()

        episode = Episode(row[1], row[2], row[3], row[4], row[5])
        # print(episode)

        cur.close()
        conn.close()

        return episode

    def _get_conn(self):
        return psycopg2.connect(
            database=self.config["DB_NAME"],
            host=self.config["DB_HOST"],
            user=self.config["DB_USER"],
            # password=self.config["DB_PASSWORD"],
            port=self.config["DB_PORT"],
        )
