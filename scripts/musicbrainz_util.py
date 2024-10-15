MusicBrainzArtist = dict[str, any]

def get_tags_from_musicbrainz_taglist(musicbrainz_tag_list: list[dict[str, str]]) -> list[str]:
    return ([tagObj['name'] for tagObj in musicbrainz_tag_list if 'name' in tagObj])
