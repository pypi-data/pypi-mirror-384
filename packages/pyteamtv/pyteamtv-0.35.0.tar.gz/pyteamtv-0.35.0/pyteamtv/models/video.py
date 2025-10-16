from .teamtv_object import TeamTVObject


class Video(TeamTVObject):
    @property
    def video_id(self):
        return self._video_id

    @property
    def parts(self):
        return self._parts

    @property
    def media_url(self):
        return self._media_url

    @property
    def state(self):
        return self._state

    @property
    def tags(self):
        return self._tags

    @property
    def skip_transcoding(self):
        return self._skip_transcoding

    @property
    def livestream(self):
        return self._livestream

    @property
    def is_upload_completed(self):
        return (
            all(part["state"] != "new" for part in self._parts) and len(self._parts) > 0
        )

    def __repr__(self):
        return f"<Video video_id={self.video_id} state={self.state}>"

    def _use_attributes(self, attributes: dict):
        self._video_id = attributes["videoId"]
        self._parts = attributes["parts"]
        self._media_url = attributes.get("mediaUrl")
        self._state = attributes["state"]
        self._tags = attributes.get("tags", {})
        self._livestream = attributes.get("livestream", {})
        self._skip_transcoding = attributes.get("skipTranscoding", False)

        super()._use_attributes(attributes)
